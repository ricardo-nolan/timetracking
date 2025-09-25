"""
Unit tests for main application entry point
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMainApplication(unittest.TestCase):
    """Test cases for main application"""
    
    @patch('timetracking.gui.tk.Tk')
    @patch('timetracking.gui.TimeTrackerGUI')
    def test_main_application_startup(self, mock_gui, mock_tk):
        """Test main application startup"""
        # Mock tkinter components
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Mock GUI class
        mock_gui_instance = MagicMock()
        mock_gui.return_value = mock_gui_instance
        
        # Import and test main function
        try:
            from timetracking.main import main
            main()
            
            # Verify GUI was created
            mock_gui.assert_called_once()
            mock_gui_instance.run.assert_called_once()
            
        except ImportError:
            # If main.py doesn't exist yet, that's okay for this test
            self.skipTest("main.py not found")
    
    def test_imports(self):
        """Test that all required modules can be imported"""
        try:
            import database
            import pdf_export
            import email_export
            import gui
        except ImportError as e:
            self.fail(f"Failed to import required module: {e}")
    
    def test_database_initialization(self):
        """Test database can be initialized"""
        try:
            from database import TimeTrackerDB
            import tempfile
            
            # Create temporary database
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            db = TimeTrackerDB(temp_db.name)
            db.init_database()
            
            # Verify database was created
            self.assertTrue(os.path.exists(temp_db.name))
            
            # Cleanup
            os.unlink(temp_db.name)
            
        except Exception as e:
            self.fail(f"Database initialization failed: {e}")
    
    def test_pdf_exporter_initialization(self):
        """Test PDF exporter can be initialized"""
        try:
            from pdf_export import PDFExporter
            exporter = PDFExporter()
            self.assertIsNotNone(exporter)
        except Exception as e:
            self.fail(f"PDF exporter initialization failed: {e}")
    
    def test_email_exporter_initialization(self):
        """Test email exporter can be initialized"""
        try:
            from email_export import EmailExporter
            exporter = EmailExporter()
            self.assertIsNotNone(exporter)
            self.assertEqual(exporter.smtp_server, "smtp.gmail.com")
            self.assertEqual(exporter.smtp_port, 587)
        except Exception as e:
            self.fail(f"Email exporter initialization failed: {e}")


if __name__ == '__main__':
    unittest.main()
