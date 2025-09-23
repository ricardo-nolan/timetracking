"""
Unit tests for database operations
"""
import unittest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timetracking.database import TimeTrackerDB


class TestTimeTrackerDB(unittest.TestCase):
    """Test cases for TimeTrackerDB class"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = TimeTrackerDB(self.temp_db.name)
        self.db.init_database()
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_init_database(self):
        """Test database initialization"""
        # Check if tables exist
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Check projects table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Check time_entries table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='time_entries'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Check project_emails table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_emails'")
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    def test_add_project(self):
        """Test adding a project"""
        project_id = self.db.add_project("Test Project", "Test Description", "test@example.com")
        self.assertIsInstance(project_id, int)
        self.assertGreater(project_id, 0)
    
    def test_get_projects(self):
        """Test retrieving projects"""
        # Add test projects
        self.db.add_project("Project 1", "Description 1", "email1@example.com")
        self.db.add_project("Project 2", "Description 2", "email2@example.com")
        
        projects = self.db.get_projects()
        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0][1], "Project 1")  # name
        self.assertEqual(projects[1][1], "Project 2")  # name
    
    def test_start_stop_timer(self):
        """Test starting and stopping a timer"""
        # Add a project first
        project_id = self.db.add_project("Test Project", "Test Description", "test@example.com")
        
        # Start timer
        entry_id = self.db.start_timer(project_id, "Test task")
        self.assertIsInstance(entry_id, int)
        self.assertGreater(entry_id, 0)
        
        # Stop timer
        result = self.db.stop_timer(project_id)
        self.assertIsNotNone(result)
    
    def test_get_time_entries(self):
        """Test retrieving time entries"""
        # Add project and time entry
        project_id = self.db.add_project("Test Project", "Test Description", "test@example.com")
        
        # Start and stop timer
        self.db.start_timer(project_id, "Test task")
        self.db.stop_timer(project_id)
        
        entries = self.db.get_time_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][3], "Test task")  # description
    
    def test_update_entry(self):
        """Test updating a time entry"""
        # Add project and time entry
        project_id = self.db.add_project("Test Project", "Test Description", "test@example.com")
        
        # Start and stop timer
        entry_id = self.db.start_timer(project_id, "Original task")
        self.db.stop_timer(project_id)
        
        # Update entry
        new_description = "Updated task"
        success = self.db.update_entry(entry_id, description=new_description)
        
        self.assertTrue(success)
        
        # Verify update
        entry = self.db.get_entry(entry_id)
        self.assertEqual(entry[3], new_description)  # description
    
    def test_delete_entry(self):
        """Test deleting a time entry"""
        # Add project and time entry
        project_id = self.db.add_project("Test Project", "Test Description", "test@example.com")
        
        # Start and stop timer
        entry_id = self.db.start_timer(project_id, "Test task")
        self.db.stop_timer(project_id)
        
        # Delete entry
        success = self.db.delete_entry(entry_id)
        self.assertTrue(success)
        
        # Verify deletion
        entry = self.db.get_entry(entry_id)
        self.assertIsNone(entry)
    
    def test_add_project_email(self):
        """Test adding project email"""
        # Add project
        project_id = self.db.add_project("Test Project", "Test Description", "test@example.com")
        
        # Add project email
        email_id = self.db.add_project_email(project_id, "additional@example.com", is_primary=False)
        self.assertIsInstance(email_id, int)
        self.assertGreater(email_id, 0)
    
    def test_get_project_emails(self):
        """Test retrieving project emails"""
        # Add project and emails
        project_id = self.db.add_project("Test Project", "Test Description", "test@example.com")
        self.db.add_project_email(project_id, "email1@example.com", is_primary=True)
        self.db.add_project_email(project_id, "email2@example.com", is_primary=False)
        
        emails = self.db.get_project_emails(project_id)
        self.assertEqual(len(emails), 2)
        self.assertTrue(emails[0][2])  # is_primary for first email
        self.assertFalse(emails[1][2])  # is_primary for second email
    
    def test_update_project(self):
        """Test updating project"""
        # Add project
        project_id = self.db.add_project("Original Name", "Original Description", "test@example.com")
        
        # Update project
        success = self.db.update_project(project_id, name="Updated Name", description="Updated Description")
        self.assertTrue(success)
        
        # Verify update
        projects = self.db.get_projects()
        updated_project = next(p for p in projects if p[0] == project_id)
        self.assertEqual(updated_project[1], "Updated Name")
        self.assertEqual(updated_project[2], "Updated Description")


if __name__ == '__main__':
    unittest.main()
