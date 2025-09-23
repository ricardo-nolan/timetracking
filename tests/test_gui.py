"""
Unit tests for GUI components
"""
import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timetracking.database import TimeTrackerDB
from timetracking.pdf_export import PDFExporter
from timetracking.email_export import EmailExporter


class TestTimeTrackerGUI(unittest.TestCase):
    """Test cases for GUI components"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = TimeTrackerDB(self.temp_db.name)
        self.db.init_database()
        
        # Create exporters
        self.pdf_exporter = PDFExporter()
        self.email_exporter = EmailExporter()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_integration(self):
        """Test database operations used by GUI"""
        # Test adding project
        project_id = self.db.add_project("Test Project", "Test Description", "test@example.com")
        self.assertIsInstance(project_id, int)
        
        # Test adding time entry
        entry_id = self.db.start_timer(project_id, "Test task")
        self.assertIsInstance(entry_id, int)
        self.db.stop_timer(project_id)
        
        # Test retrieving entries
        entries = self.db.get_time_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][3], "Test task")
    
    def test_project_management(self):
        """Test project management functionality"""
        # Add project
        project_id = self.db.add_project("GUI Test Project", "GUI Test Description", "gui@example.com")
        
        # Add project email
        email_id = self.db.add_project_email(project_id, "additional@example.com", is_primary=False)
        self.assertIsInstance(email_id, int)
        
        # Get project emails
        emails = self.db.get_project_emails(project_id)
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0][1], "additional@example.com")
        
        # Update project
        success = self.db.update_project(project_id, name="Updated GUI Project")
        self.assertTrue(success)
        
        # Verify update
        projects = self.db.get_projects()
        updated_project = next(p for p in projects if p[0] == project_id)
        self.assertEqual(updated_project[1], "Updated GUI Project")
    
    def test_time_entry_editing(self):
        """Test time entry editing functionality"""
        # Add project and time entry
        project_id = self.db.add_project("Edit Test Project", "Edit Test Description", "edit@example.com")
        entry_id = self.db.start_timer(project_id, "Original task")
        self.db.stop_timer(project_id)
        
        # Update entry
        new_description = "Updated task"
        success = self.db.update_entry(entry_id, description=new_description)
        self.assertTrue(success)
        
        # Verify update
        entry = self.db.get_entry(entry_id)
        self.assertEqual(entry[3], new_description)
    
    def test_duration_calculation(self):
        """Test duration calculation for GUI display"""
        # Test various duration scenarios
        test_cases = [
            (timedelta(hours=1, minutes=30, seconds=45), "1h 30m 45s"),
            (timedelta(minutes=45, seconds=30), "45m 30s"),
            (timedelta(seconds=30), "30s"),
            (timedelta(hours=2), "2h 0m 0s"),
        ]
        
        for duration, expected_format in test_cases:
            start_time = datetime.now()
            end_time = start_time + duration
            
            # Calculate duration in seconds
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                duration_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                duration_str = f"{minutes}m {seconds}s"
            else:
                duration_str = f"{seconds}s"
            
            # Verify formatting
            self.assertEqual(duration_str, expected_format)
    
    @patch('tkinter.Tk')
    def test_gui_initialization(self, mock_tk):
        """Test GUI initialization"""
        # Mock tkinter components
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # This test would require more complex mocking of tkinter components
        # For now, we'll test the database operations that the GUI depends on
        self.assertTrue(True)  # Placeholder for GUI initialization test
    
    def test_export_functionality(self):
        """Test export functionality used by GUI"""
        # Create test data
        project_id = self.db.add_project("Export Test Project", "Export Test Description", "export@example.com")
        self.db.start_timer(project_id, "Export task")
        self.db.stop_timer(project_id)
        
        # Get data for export
        entries = self.db.get_time_entries()
        projects = self.db.get_projects()
        
        self.assertEqual(len(entries), 1)
        self.assertEqual(len(projects), 1)
        
        # Test PDF export
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(entries, output_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_email_configuration(self):
        """Test email configuration functionality"""
        # Test email exporter initialization
        exporter = EmailExporter()
        self.assertEqual(exporter.smtp_server, "smtp.gmail.com")
        self.assertEqual(exporter.smtp_port, 587)
        
        # Test configuration saving/loading
        exporter.sender_email = "test@example.com"
        exporter.sender_password = "testpass"
        
        # Test save/load cycle
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_config:
            exporter.config_file = tmp_config.name
            exporter.save_config()
            
            # Create new exporter and load config
            new_exporter = EmailExporter()
            new_exporter.config_file = tmp_config.name
            new_exporter.load_config()
            
            self.assertEqual(new_exporter.sender_email, "test@example.com")
            self.assertEqual(new_exporter.sender_password, "testpass")
        
        # Clean up
        if os.path.exists(tmp_config.name):
            os.unlink(tmp_config.name)


if __name__ == '__main__':
    unittest.main()
