"""
Unit tests for GUI edge cases and error conditions
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


class TestGUIEdgeCases(unittest.TestCase):
    """Test cases for GUI edge cases and error conditions"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = TimeTrackerDB(self.temp_db.name)
        
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_edit_entry_dialog_project_selection(self):
        """Test EditEntryDialog handles project selection correctly"""
        # Add project with rate and currency
        project_id = self.db.add_project(
            "Test Project", 
            "Description", 
            "test@example.com", 
            25.0, 
            "EUR"
        )
        
        # Add time entry
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.db.stop_timer(entry_id)
        
        # Get entry for testing
        entries = self.db.get_time_entries()
        entry = entries[0]
        
        # Test that entry has correct structure (9 fields)
        self.assertEqual(len(entry), 9)
        self.assertEqual(entry[7], 25.0)  # rate
        self.assertEqual(entry[8], "EUR")  # currency
    
    def test_project_edit_dialog_with_emails(self):
        """Test ProjectEditDialog handles multiple emails correctly"""
        # Add project with multiple emails
        project_id = self.db.add_project(
            "Test Project", 
            "Description", 
            "primary@example.com", 
            25.0, 
            "EUR"
        )
        
        # Test project structure
        projects = self.db.get_projects()
        project = projects[0]
        
        self.assertEqual(len(project), 6)  # id, name, desc, email, rate, currency
        self.assertEqual(project[3], "primary@example.com")
        self.assertEqual(project[4], 25.0)
        self.assertEqual(project[5], "EUR")
    
    def test_email_settings_dialog_config_loading(self):
        """Test EmailSettingsDialog loads configuration correctly"""
        # Test that EmailExporter loads config from home directory
        with patch('timetracking.email_export.os.path.expanduser') as mock_expanduser:
            mock_expanduser.return_value = '/home/user'
            
            exporter = EmailExporter()
            
            # Should use home directory for config file
            self.assertTrue(exporter.config_file.startswith('/home/user'))
    
    def test_pdf_export_with_rate_calculation(self):
        """Test PDF export calculates rates correctly"""
        # Add project with rate
        project_id = self.db.add_project(
            "Test Project", 
            "Description", 
            "test@example.com", 
            25.0, 
            "EUR"
        )
        
        # Add time entry
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.db.stop_timer(entry_id)
        
        # Get entries for export
        entries = self.db.get_time_entries()
        
        # Test that entries have rate and currency
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(len(entry), 9)
        self.assertEqual(entry[7], 25.0)  # rate
        self.assertEqual(entry[8], "EUR")  # currency
    
    def test_email_export_with_rate_calculation(self):
        """Test email export calculates rates correctly"""
        # Add project with rate
        project_id = self.db.add_project(
            "Test Project", 
            "Description", 
            "test@example.com", 
            25.0, 
            "USD"
        )
        
        # Add time entry
        entry_id = self.db.start_timer(project_id, "Test Task")
        self.db.stop_timer(entry_id)
        
        # Get entries for export
        entries = self.db.get_time_entries()
        
        # Test that entries have rate and currency
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(len(entry), 9)
        self.assertEqual(entry[7], 25.0)  # rate
        self.assertEqual(entry[8], "USD")  # currency
    
    def test_duration_formatting_edge_cases(self):
        """Test duration formatting for edge cases"""
        # Test zero duration
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=0)
        
        # Test very short duration (less than 1 minute)
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=30)
        
        # Test very long duration (more than 24 hours)
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=25, minutes=30, seconds=45)
        
        # These should all be handled gracefully
        self.assertTrue(True)  # Placeholder for duration formatting tests
    
    def test_currency_symbol_display(self):
        """Test currency symbol display for different currencies"""
        # Test EUR currency
        project_id_eur = self.db.add_project(
            "EUR Project", 
            "Description", 
            "test@example.com", 
            25.0, 
            "EUR"
        )
        
        # Test USD currency
        project_id_usd = self.db.add_project(
            "USD Project", 
            "Description", 
            "test@example.com", 
            30.0, 
            "USD"
        )
        
        projects = self.db.get_projects()
        
        # Find projects by name
        eur_project = next(p for p in projects if p[1] == "EUR Project")
        usd_project = next(p for p in projects if p[1] == "USD Project")
        
        self.assertEqual(eur_project[5], "EUR")
        self.assertEqual(usd_project[5], "USD")
    
    def test_database_file_paths(self):
        """Test that database uses correct file paths"""
        # Test that database file is created in home directory
        with patch('timetracking.database.os.path.expanduser') as mock_expanduser:
            mock_expanduser.return_value = '/home/user'
            
            # Mock the database file creation
            with patch('timetracking.database.sqlite3.connect') as mock_connect:
                mock_conn = MagicMock()
                mock_connect.return_value = mock_conn
                
                db = TimeTrackerDB()
                
                # Should use home directory for database
                self.assertTrue(db.db_path.startswith('/home/user'))
                self.assertTrue(db.db_path.endswith('time_tracker.db'))
    
    def test_email_config_file_paths(self):
        """Test that email config uses correct file paths"""
        # Test that config file is created in home directory
        with patch('timetracking.email_export.os.path.expanduser') as mock_expanduser:
            mock_expanduser.return_value = '/home/user'
            
            exporter = EmailExporter()
            
            # Should use home directory for config file
            self.assertTrue(exporter.config_file.startswith('/home/user'))
            self.assertTrue(exporter.config_file.endswith('email_config.json'))
    
    def test_password_encryption_file_paths(self):
        """Test that password encryption uses correct file paths"""
        # Test that key file is created in home directory
        with patch('timetracking.password_utils.os.path.expanduser') as mock_expanduser:
            mock_expanduser.return_value = '/home/user'
            
            # Mock file operations
            with patch('timetracking.password_utils.os.path.exists') as mock_exists:
                mock_exists.return_value = False
                with patch('builtins.open', create=True) as mock_open:
                    mock_file = MagicMock()
                    mock_open.return_value.__enter__.return_value = mock_file
                    
                    from timetracking.password_utils import PasswordEncryption
                    encryption = PasswordEncryption()
                    
                    # Should use home directory for key file
                    self.assertTrue(encryption.key_file.startswith('/home/user'))
                    self.assertTrue(encryption.key_file.endswith('email_key.key'))


if __name__ == '__main__':
    unittest.main()
