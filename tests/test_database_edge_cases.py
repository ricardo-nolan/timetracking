"""
Unit tests for database edge cases and error conditions
"""
import unittest
import tempfile
import os
import sys
import sqlite3
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timetracking.database import TimeTrackerDB


class TestDatabaseEdgeCases(unittest.TestCase):
    """Test cases for database edge cases and error conditions"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = TimeTrackerDB(self.temp_db.name)
        
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_add_project_with_rate_and_currency(self):
        """Test adding project with rate and currency"""
        project_id = self.db.add_project(
            "Test Project", 
            "Description", 
            "test@example.com", 
            25.0, 
            "USD"
        )
        
        self.assertIsInstance(project_id, int)
        self.assertGreater(project_id, 0)
        
        projects = self.db.get_projects()
        self.assertEqual(len(projects), 1)
        
        project = projects[0]
        self.assertEqual(project[0], project_id)  # id
        self.assertEqual(project[1], "Test Project")  # name
        self.assertEqual(project[2], "Description")  # description
        self.assertEqual(project[3], "test@example.com")  # email
        self.assertEqual(project[4], 25.0)  # rate
        self.assertEqual(project[5], "USD")  # currency
    
    def test_add_project_without_rate(self):
        """Test adding project without rate"""
        project_id = self.db.add_project("Test Project", "Description")
        
        projects = self.db.get_projects()
        project = projects[0]
        self.assertIsNone(project[4])  # rate should be None
        self.assertEqual(project[5], "EUR")  # default currency
    
    def test_update_project_rate_and_currency(self):
        """Test updating project rate and currency"""
        project_id = self.db.add_project("Test Project", "Description")
        
        success = self.db.update_project(
            project_id, 
            rate=30.0, 
            currency="USD"
        )
        
        self.assertTrue(success)
        
        projects = self.db.get_projects()
        project = projects[0]
        self.assertEqual(project[4], 30.0)  # rate
        self.assertEqual(project[5], "USD")  # currency
    
    def test_get_latest_entry_project(self):
        """Test getting latest entry project"""
        # No entries yet
        latest = self.db.get_latest_entry_project()
        self.assertIsNone(latest)
        
        # Add project and entry
        project_id = self.db.add_project("Test Project", "Description")
        self.db.start_timer(project_id, "Test Task")
        
        latest = self.db.get_latest_entry_project()
        self.assertEqual(latest, project_id)
    
    def test_time_entries_with_rate_and_currency(self):
        """Test getting time entries with rate and currency"""
        project_id = self.db.add_project(
            "Test Project", 
            "Description", 
            "test@example.com", 
            25.0, 
            "EUR"
        )
        
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.db.stop_timer(entry_id)
        
        entries = self.db.get_time_entries()
        self.assertEqual(len(entries), 1)
        
        entry = entries[0]
        self.assertEqual(len(entry), 9)  # Should have 9 fields
        self.assertEqual(entry[7], 25.0)  # rate
        self.assertEqual(entry[8], "EUR")  # currency
    
    def test_database_migration_rate_currency(self):
        """Test database migration for rate and currency columns"""
        # Close existing connection and remove database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        # Create a database without rate/currency columns
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
    
    def test_invalid_project_id(self):
        """Test operations with invalid project ID"""
        # Try to start timer with invalid project ID - should return None
        result = self.db.start_timer(999, "Test Task")
        self.assertIsNone(result)
        
        # Try to update invalid project
        success = self.db.update_project(999, name="New Name")
        self.assertFalse(success)
    
    def test_duplicate_project_name(self):
        """Test adding project with duplicate name"""
        self.db.add_project("Test Project", "Description")
        
        with self.assertRaises(ValueError):
            self.db.add_project("Test Project", "Another Description")
    
    def test_stop_nonexistent_timer(self):
        """Test stopping nonexistent timer"""
        duration = self.db.stop_timer(999)
        self.assertIsNone(duration)
    
    def test_get_entries_with_filters(self):
        """Test getting entries with various filters"""
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
        
        # Test running entries only (filter by end_time is None)
        entries = self.db.get_time_entries()
        running_entries = [e for e in entries if e[5] is None]  # end_time is None
        self.assertEqual(len(running_entries), 1)
        self.assertIsNone(running_entries[0][5])  # end_time should be None


if __name__ == '__main__':
    unittest.main()
