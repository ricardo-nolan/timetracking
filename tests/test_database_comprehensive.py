"""
Comprehensive database tests to improve coverage
"""
import unittest
import tempfile
import os
import sys
import sqlite3
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timetracking.database import TimeTrackerDB


class TestDatabaseComprehensive(unittest.TestCase):
    """Comprehensive test cases for database functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = TimeTrackerDB(self.temp_db.name)
        
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_add_project_emails(self):
        """Test adding multiple emails to a project"""
        project_id = self.db.add_project("Test Project", "Description")
        
        # Add emails
        self.db.add_project_email(project_id, "email1@example.com")
        self.db.add_project_email(project_id, "email2@example.com")
        
        emails = self.db.get_project_emails(project_id)
        self.assertEqual(len(emails), 2)
        self.assertIn("email1@example.com", [email[1] for email in emails])
        self.assertIn("email2@example.com", [email[1] for email in emails])
    
    def test_set_primary_email(self):
        """Test setting primary email"""
        project_id = self.db.add_project("Test Project", "Description")
        
        # Add emails
        self.db.add_project_email(project_id, "email1@example.com")
        self.db.add_project_email(project_id, "email2@example.com")
        
        # Set first email as primary
        emails = self.db.get_project_emails(project_id)
        self.db.set_primary_email(project_id, emails[0][0])
        
        # Check primary status
        emails = self.db.get_project_emails(project_id)
        primary_emails = [email for email in emails if email[2]]  # is_primary
        self.assertEqual(len(primary_emails), 1)
        self.assertEqual(primary_emails[0][1], "email1@example.com")
    
    def test_remove_project_email(self):
        """Test removing project email"""
        project_id = self.db.add_project("Test Project", "Description")
        
        # Add email
        self.db.add_project_email(project_id, "email1@example.com")
        emails = self.db.get_project_emails(project_id)
        email_id = emails[0][0]
        
        # Remove email
        self.db.remove_project_email(project_id, email_id)
        
        emails = self.db.get_project_emails(project_id)
        self.assertEqual(len(emails), 0)
    
    def test_get_time_entries_with_filters(self):
        """Test getting time entries with various filters"""
        project_id = self.db.add_project("Test Project", "Description")
        
        # Add entries
        entry1 = self.db.start_timer(project_id, "Task 1")
        self.db.stop_timer(entry1)
        
        entry2 = self.db.start_timer(project_id, "Task 2")
        
        # Test date range filter
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        
        entries = self.db.get_time_entries(
            start_date=start_date,
            end_date=end_date
        )
        self.assertEqual(len(entries), 2)
        
        # Test project filter
        entries = self.db.get_time_entries(project_id=project_id)
        self.assertEqual(len(entries), 2)
    
    def test_update_entry_comprehensive(self):
        """Test comprehensive entry updates"""
        project_id = self.db.add_project("Test Project", "Description")
        entry_id = self.db.start_timer(project_id, "Original Task")
        self.db.stop_timer(entry_id)
        
        # Update description
        success = self.db.update_entry(entry_id, description="Updated Task")
        self.assertTrue(success)
        
        # Update start time
        new_start = datetime.now() - timedelta(hours=2)
        success = self.db.update_entry(entry_id, start_time=new_start)
        self.assertTrue(success)
        
        # Update end time
        new_end = datetime.now() - timedelta(hours=1)
        success = self.db.update_entry(entry_id, end_time=new_end)
        self.assertTrue(success)
        
        # Verify updates
        entries = self.db.get_time_entries()
        entry = entries[0]
        self.assertEqual(entry[3], "Updated Task")  # description
    
    def test_database_error_handling(self):
        """Test database error handling"""
        # Test invalid project operations
        result = self.db.start_timer(999, "Test Task")
        self.assertIsNone(result)
        
        # Test invalid entry operations
        success = self.db.update_entry(999, description="Test")
        self.assertFalse(success)
        
        success = self.db.delete_entry(999)
        self.assertFalse(success)
    
    def test_project_operations_comprehensive(self):
        """Test comprehensive project operations"""
        # Add project
        project_id = self.db.add_project("Test Project", "Description", "test@example.com", 25.0, "EUR")
        
        # Update project
        success = self.db.update_project(project_id, name="Updated Project", rate=30.0, currency="USD")
        self.assertTrue(success)
        
        # Get project details
        projects = self.db.get_projects()
        project = projects[0]
        self.assertEqual(project[1], "Updated Project")
        self.assertEqual(project[4], 30.0)
        self.assertEqual(project[5], "USD")
    
    def test_time_entry_operations_comprehensive(self):
        """Test comprehensive time entry operations"""
        project_id = self.db.add_project("Test Project", "Description")
        
        # Start timer
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.assertIsNotNone(entry_id)
        
        # Get running entries
        entries = self.db.get_time_entries()
        running_entries = [e for e in entries if e[5] is None]  # end_time is None
        self.assertEqual(len(running_entries), 1)
        
        # Stop timer
        duration = self.db.stop_timer(entry_id)
        self.assertIsNotNone(duration)
        self.assertGreaterEqual(duration, 0)
        
        # Verify entry is no longer running
        entries = self.db.get_time_entries()
        running_entries = [e for e in entries if e[5] is None]
        self.assertEqual(len(running_entries), 0)
    
    def test_database_initialization_edge_cases(self):
        """Test database initialization edge cases"""
        # Test with custom database path
        custom_db = tempfile.NamedTemporaryFile(delete=False)
        custom_db.close()
        
        try:
            db = TimeTrackerDB(custom_db.name)
            self.assertEqual(db.db_path, custom_db.name)
            
            # Test that tables are created
            conn = sqlite3.connect(custom_db.name)
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
        finally:
            if os.path.exists(custom_db.name):
                os.unlink(custom_db.name)
    
    def test_database_migration_comprehensive(self):
        """Test comprehensive database migration"""
        # Create database without new columns
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Create old schema
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                default_email TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE time_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                description TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_minutes INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Initialize database (should migrate)
        db = TimeTrackerDB(self.temp_db.name)
        
        # Check that columns were added
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]
        
        self.assertIn("rate", columns)
        self.assertIn("currency", columns)
        
        conn.close()


if __name__ == '__main__':
    unittest.main()
