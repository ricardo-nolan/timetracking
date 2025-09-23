"""
Integration tests for complete workflows
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


class TestTimeTrackerIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""
    
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
    
    def test_complete_time_tracking_workflow(self):
        """Test complete time tracking workflow"""
        # 1. Add project
        project_id = self.db.add_project("Integration Test Project", "Integration Test Description", "integration@example.com")
        self.assertIsInstance(project_id, int)
        
        # 2. Add project email
        email_id = self.db.add_project_email(project_id, "additional@example.com", is_primary=False)
        self.assertIsInstance(email_id, int)
        
        # 3. Start time tracking (add time entry)
        entry_id = self.db.start_timer(project_id, "Integration test task")
        self.assertIsInstance(entry_id, int)
        
        # 4. Stop time tracking
        duration = self.db.stop_timer(project_id)
        self.assertIsNotNone(duration)
        self.assertGreaterEqual(duration, 0)  # Allow 0 duration for very fast operations
        
        # 5. Verify entry was created correctly
        entry = self.db.get_entry(entry_id)
        self.assertEqual(entry[3], "Integration test task")
        
        # 6. Get all entries for export
        entries = self.db.get_time_entries()
        projects = self.db.get_projects()
        
        self.assertEqual(len(entries), 1)
        self.assertEqual(len(projects), 1)
    
    def test_pdf_export_workflow(self):
        """Test complete PDF export workflow"""
        # Create test data
        project_id = self.db.add_project("PDF Test Project", "PDF Test Description", "pdf@example.com")
        
        # Add multiple time entries
        for i, description in enumerate(["Task 1", "Task 2", "Task 3"]):
            self.db.start_timer(project_id, description)
            self.db.stop_timer(project_id)
        
        # Get data for export
        entries = self.db.get_time_entries()
        projects = self.db.get_projects()
        
        # Export to PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(entries, output_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
            self.assertGreater(os.path.getsize(output_path), 0)
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    @patch('smtplib.SMTP')
    def test_email_export_workflow(self, mock_smtp):
        """Test complete email export workflow"""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Create test data
        project_id = self.db.add_project("Email Test Project", "Email Test Description", "email@example.com")
        self.db.add_project_email(project_id, "additional@example.com", is_primary=False)
        
        # Add time entries
        self.db.start_timer(project_id, "Email Task 1")
        self.db.stop_timer(project_id)
        self.db.start_timer(project_id, "Email Task 2")
        self.db.stop_timer(project_id)
        
        # Get data for export
        entries = self.db.get_time_entries()
        projects = self.db.get_projects()
        
        # Configure email exporter
        self.email_exporter.sender_email = "test@example.com"
        self.email_exporter.sender_password = "testpass"
        
        # Send email
        success = self.email_exporter.send_time_report(
            entries,
            "test@example.com",
            "testpass",
            "recipient@example.com"
        )
        
        self.assertTrue(success)
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "testpass")
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
    
    def test_time_entry_editing_workflow(self):
        """Test complete time entry editing workflow"""
        # Create project and time entry
        project_id = self.db.add_project("Edit Test Project", "Edit Test Description", "edit@example.com")
        entry_id = self.db.start_timer(project_id, "Original task")
        self.db.stop_timer(project_id)
        
        # Edit the entry
        new_description = "Updated task description"
        
        success = self.db.update_entry(
            entry_id,
            description=new_description
        )
        self.assertTrue(success)
        
        # Verify changes
        entry = self.db.get_entry(entry_id)
        self.assertEqual(entry[3], new_description)
    
    def test_project_management_workflow(self):
        """Test complete project management workflow"""
        # Create project
        project_id = self.db.add_project("Project Management Test", "Project Management Description", "pm@example.com")
        
        # Add multiple emails
        email1_id = self.db.add_project_email(project_id, "primary@example.com", is_primary=True)
        email2_id = self.db.add_project_email(project_id, "secondary@example.com", is_primary=False)
        email3_id = self.db.add_project_email(project_id, "tertiary@example.com", is_primary=False)
        
        # Get project emails
        emails = self.db.get_project_emails(project_id)
        self.assertEqual(len(emails), 3)
        
        # Verify primary email
        primary_emails = [email for email in emails if email[2]]  # is_primary=True
        self.assertEqual(len(primary_emails), 1)
        self.assertEqual(primary_emails[0][1], "primary@example.com")
        
        # Update project
        success = self.db.update_project(
            project_id,
            name="Updated Project Management Test",
            description="Updated Project Management Description"
        )
        self.assertTrue(success)
        
        # Verify update
        projects = self.db.get_projects()
        updated_project = next(p for p in projects if p[0] == project_id)
        self.assertEqual(updated_project[1], "Updated Project Management Test")
        self.assertEqual(updated_project[2], "Updated Project Management Description")
    
    def test_database_migration_workflow(self):
        """Test database migration workflow"""
        # This test verifies that the database can handle schema changes
        # The init_database method should handle adding new columns
        
        # Create a new database instance (simulating migration)
        new_db = TimeTrackerDB(self.temp_db.name)
        new_db.init_database()  # This should handle any missing columns
        
        # Verify tables exist
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Check all required tables exist
        tables = ['projects', 'time_entries', 'project_emails']
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    def test_error_handling_workflow(self):
        """Test error handling in various scenarios"""
        # Test invalid project ID
        invalid_entry = self.db.get_entry(99999)
        self.assertIsNone(invalid_entry)
        
        # Test invalid project ID for emails
        invalid_emails = self.db.get_project_emails(99999)
        self.assertEqual(len(invalid_emails), 0)
        
        # Test updating non-existent entry
        success = self.db.update_entry(99999, description="This should fail")
        self.assertFalse(success)
        
        # Test deleting non-existent entry
        success = self.db.delete_entry(99999)
        self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()
