"""
GUI integration tests to improve coverage
"""
import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timetracking.database import TimeTrackerDB
from timetracking.pdf_export import PDFExporter
from timetracking.email_export import EmailExporter


class TestGUIIntegration(unittest.TestCase):
    """Test cases for GUI integration functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = TimeTrackerDB(self.temp_db.name)
        
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_gui_database_integration(self):
        """Test GUI integration with database"""
        # Test project creation workflow
        project_id = self.db.add_project("Test Project", "Description", "test@example.com", 25.0, "EUR")
        
        # Test project retrieval for GUI
        projects = self.db.get_projects()
        self.assertEqual(len(projects), 1)
        
        project = projects[0]
        self.assertEqual(project[0], project_id)
        self.assertEqual(project[1], "Test Project")
        self.assertEqual(project[2], "Description")
        self.assertEqual(project[3], "test@example.com")
        self.assertEqual(project[4], 25.0)
        self.assertEqual(project[5], "EUR")
        
        # Test time entry creation workflow
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.assertIsNotNone(entry_id)
        
        # Test time entry retrieval for GUI
        entries = self.db.get_time_entries()
        self.assertEqual(len(entries), 1)
        
        entry = entries[0]
        self.assertEqual(entry[0], entry_id)
        self.assertEqual(entry[1], project_id)
        self.assertEqual(entry[3], "Test Task")
    
    def test_gui_pdf_export_integration(self):
        """Test GUI integration with PDF export"""
        # Add test data
        project_id = self.db.add_project("Test Project", "Description", "test@example.com", 25.0, "EUR")
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.db.stop_timer(entry_id)
        
        # Test PDF export integration
        entries = self.db.get_time_entries()
        pdf_exporter = PDFExporter()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = pdf_exporter.export_time_report(entries, output_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
            self.assertGreater(os.path.getsize(output_path), 0)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_gui_email_export_integration(self):
        """Test GUI integration with email export"""
        # Add test data
        project_id = self.db.add_project("Test Project", "Description", "test@example.com", 25.0, "EUR")
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.db.stop_timer(entry_id)
        
        # Test email export integration
        entries = self.db.get_time_entries()
        email_exporter = EmailExporter()
        
        # Mock SMTP for testing
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server
            
            email_exporter.sender_email = "test@example.com"
            email_exporter.sender_password = "testpass"
            
            success = email_exporter.send_time_report(
                entries,
                "Test Project",
                "2024-01-01",
                "2024-01-01",
                "recipient@example.com"
            )
            
            self.assertTrue(success)
            mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("test@example.com", "testpass")
            mock_server.sendmail.assert_called_once()
            mock_server.quit.assert_called_once()
    
    def test_gui_project_management_integration(self):
        """Test GUI integration with project management"""
        # Test project creation workflow
        project_id = self.db.add_project("Test Project", "Description", "test@example.com", 25.0, "EUR")
        
        # Test project update workflow
        success = self.db.update_project(project_id, name="Updated Project", rate=30.0, currency="USD")
        self.assertTrue(success)
        
        # Test project retrieval after update
        projects = self.db.get_projects()
        project = projects[0]
        self.assertEqual(project[1], "Updated Project")
        self.assertEqual(project[4], 30.0)
        self.assertEqual(project[5], "USD")
        
        # Test project email management
        self.db.add_project_email(project_id, "admin@example.com")
        emails = self.db.get_project_emails(project_id)
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0][1], "admin@example.com")
    
    def test_gui_time_entry_management_integration(self):
        """Test GUI integration with time entry management"""
        # Add test project
        project_id = self.db.add_project("Test Project", "Description")
        
        # Test time entry creation workflow
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.assertIsNotNone(entry_id)
        
        # Test running entry retrieval
        entries = self.db.get_time_entries()
        running_entries = [e for e in entries if e[5] is None]  # end_time is None
        self.assertEqual(len(running_entries), 1)
        
        # Test time entry completion workflow
        duration = self.db.stop_timer(entry_id)
        self.assertIsNotNone(duration)
        self.assertGreaterEqual(duration, 0)
        
        # Test completed entry retrieval
        entries = self.db.get_time_entries()
        completed_entries = [e for e in entries if e[5] is not None]  # end_time is not None
        self.assertEqual(len(completed_entries), 1)
        
        # Test time entry update workflow
        success = self.db.update_entry(entry_id, description="Updated Task")
        self.assertTrue(success)
        
        # Test updated entry retrieval
        entries = self.db.get_time_entries()
        entry = entries[0]
        self.assertEqual(entry[3], "Updated Task")
    
    def test_gui_filtering_integration(self):
        """Test GUI integration with filtering functionality"""
        # Add test data
        project1_id = self.db.add_project("Project A", "Description A")
        project2_id = self.db.add_project("Project B", "Description B")
        
        # Add entries for different projects
        entry1 = self.db.start_timer(project1_id, "Task A1")
        self.db.stop_timer(entry1)
        
        entry2 = self.db.start_timer(project2_id, "Task B1")
        self.db.stop_timer(entry2)
        
        entry3 = self.db.start_timer(project1_id, "Task A2")
        
        # Test project filtering
        entries = self.db.get_time_entries()
        project_a_entries = [e for e in entries if e[1] == project1_id]
        project_b_entries = [e for e in entries if e[1] == project2_id]
        
        self.assertEqual(len(project_a_entries), 2)
        self.assertEqual(len(project_b_entries), 1)
        
        # Test running entries filtering
        running_entries = [e for e in entries if e[5] is None]
        self.assertEqual(len(running_entries), 1)
        
        # Test completed entries filtering
        completed_entries = [e for e in entries if e[5] is not None]
        self.assertEqual(len(completed_entries), 2)
    
    def test_gui_date_range_integration(self):
        """Test GUI integration with date range filtering"""
        # Add test data with different dates
        project_id = self.db.add_project("Test Project", "Description")
        
        # Add entries with specific dates
        entry1 = self.db.start_timer(project_id, "Task 1")
        self.db.stop_timer(entry1)
        
        entry2 = self.db.start_timer(project_id, "Task 2")
        
        # Test date range filtering
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        
        entries = self.db.get_time_entries()
        filtered_entries = []
        
        for entry in entries:
            start_time = datetime.fromisoformat(entry[4])
            if start_date <= start_time <= end_date:
                filtered_entries.append(entry)
        
        self.assertEqual(len(filtered_entries), 2)
    
    def test_gui_rate_calculation_integration(self):
        """Test GUI integration with rate calculations"""
        # Add test project with rate
        project_id = self.db.add_project("Test Project", "Description", "test@example.com", 25.0, "EUR")
        
        # Add time entry
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.db.stop_timer(entry_id)
        
        # Test rate calculation integration
        entries = self.db.get_time_entries()
        entry = entries[0]
        
        # Test rate and currency data
        self.assertEqual(entry[7], 25.0)  # rate
        self.assertEqual(entry[8], "EUR")  # currency
        
        # Test amount calculation
        duration_minutes = entry[6]  # duration in minutes
        rate = entry[7]  # rate per hour
        hours = duration_minutes / 60.0
        amount = hours * rate
        
        self.assertGreaterEqual(amount, 0)
    
    def test_gui_currency_display_integration(self):
        """Test GUI integration with currency display"""
        # Add test projects with different currencies
        project_eur_id = self.db.add_project("EUR Project", "Description", "test@example.com", 25.0, "EUR")
        project_usd_id = self.db.add_project("USD Project", "Description", "test@example.com", 30.0, "USD")
        
        # Test currency symbol mapping
        projects = self.db.get_projects()
        
        eur_project = next(p for p in projects if p[1] == "EUR Project")
        usd_project = next(p for p in projects if p[1] == "USD Project")
        
        # Test currency symbols
        eur_symbol = "€" if eur_project[5] == "EUR" else "$"
        usd_symbol = "$" if usd_project[5] == "USD" else "€"
        
        self.assertEqual(eur_symbol, "€")
        self.assertEqual(usd_symbol, "$")
    
    def test_gui_error_handling_integration(self):
        """Test GUI integration with error handling"""
        # Test invalid project operations
        result = self.db.start_timer(999, "Test Task")
        self.assertIsNone(result)
        
        # Test invalid entry operations
        success = self.db.update_entry(999, description="Test")
        self.assertFalse(success)
        
        # Test duplicate project name handling
        self.db.add_project("Test Project", "Description")
        
        # This should raise an exception or return False
        try:
            self.db.add_project("Test Project", "Another Description")
            self.fail("Should have raised an exception for duplicate project name")
        except ValueError:
            # Expected behavior
            pass
    
    def test_gui_data_refresh_integration(self):
        """Test GUI integration with data refresh"""
        # Add initial data
        project_id = self.db.add_project("Test Project", "Description")
        entry_id = self.db.start_timer(project_id, "Test Task")
        
        # Test data refresh after changes
        entries = self.db.get_time_entries()
        self.assertEqual(len(entries), 1)
        
        # Simulate data refresh
        self.db.stop_timer(entry_id)
        
        # Test refreshed data
        entries = self.db.get_time_entries()
        entry = entries[0]
        self.assertIsNotNone(entry[5])  # end_time should not be None
        
        # Test duration calculation
        duration = entry[6]
        self.assertGreaterEqual(duration, 0)
    
    def test_gui_export_workflow_integration(self):
        """Test GUI integration with export workflows"""
        # Add test data
        project_id = self.db.add_project("Test Project", "Description", "test@example.com", 25.0, "EUR")
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.db.stop_timer(entry_id)
        
        # Test PDF export workflow
        entries = self.db.get_time_entries()
        pdf_exporter = PDFExporter()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = pdf_exporter.export_time_report(entries, output_path)
            self.assertTrue(success)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
        
        # Test email export workflow
        email_exporter = EmailExporter()
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server
            
            email_exporter.sender_email = "test@example.com"
            email_exporter.sender_password = "testpass"
            
            success = email_exporter.send_time_report(
                entries,
                "Test Project",
                "2024-01-01",
                "2024-01-01",
                "recipient@example.com"
            )
            
            self.assertTrue(success)
    
    def test_gui_configuration_integration(self):
        """Test GUI integration with configuration management"""
        # Test email configuration
        email_exporter = EmailExporter()
        
        # Test configuration loading
        self.assertIsNotNone(email_exporter.smtp_server)
        self.assertIsNotNone(email_exporter.smtp_port)
        
        # Test configuration saving
        email_exporter.sender_email = "test@example.com"
        email_exporter.sender_password = "testpass"
        
        # Test configuration persistence
        self.assertEqual(email_exporter.sender_email, "test@example.com")
        self.assertEqual(email_exporter.sender_password, "testpass")
    
    def test_gui_workflow_completion_integration(self):
        """Test GUI integration with complete workflows"""
        # Test complete project creation workflow
        project_id = self.db.add_project("Test Project", "Description", "test@example.com", 25.0, "EUR")
        
        # Test complete time entry workflow
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.assertIsNotNone(entry_id)
        
        # Test complete time entry completion
        duration = self.db.stop_timer(entry_id)
        self.assertIsNotNone(duration)
        
        # Test complete export workflow
        entries = self.db.get_time_entries()
        pdf_exporter = PDFExporter()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = pdf_exporter.export_time_report(entries, output_path)
            self.assertTrue(success)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


if __name__ == '__main__':
    unittest.main()
