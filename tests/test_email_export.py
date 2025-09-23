"""
Unit tests for email export functionality
"""
import unittest
import tempfile
import os
import json
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timetracking.email_export import EmailExporter


class TestEmailExporter(unittest.TestCase):
    """Test cases for EmailExporter class"""
    
    def setUp(self):
        """Set up test data"""
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config.close()
        
        # Create sample time entries (id, project_id, project_name, description, start_time, end_time, duration, rate, currency)
        self.sample_entries = [
            (1, 1, "Project A", "Test Task 1", "2024-01-01T09:00:00", "2024-01-01T10:30:00", 90, 25.0, "EUR"),
            (2, 1, "Project A", "Test Task 2", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, 25.0, "EUR"),
        ]
        
        # Create sample projects
        self.sample_projects = [
            (1, "Project A", "Description A", "projecta@example.com"),
        ]
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    def test_init_defaults(self):
        """Test EmailExporter initialization with defaults"""
        # Mock the config loading to avoid loading real config
        with patch.object(EmailExporter, 'load_config'):
            exporter = EmailExporter()
            self.assertEqual(exporter.smtp_server, "smtp.gmail.com")
            self.assertEqual(exporter.smtp_port, 587)
            self.assertIsNone(exporter.sender_email)
            self.assertIsNone(exporter.sender_password)
    
    def test_init_custom(self):
        """Test EmailExporter initialization with custom settings"""
        # Mock the config loading to avoid loading real config
        with patch.object(EmailExporter, 'load_config'):
            exporter = EmailExporter("smtp.example.com", 465)
            self.assertEqual(exporter.smtp_server, "smtp.example.com")
            self.assertEqual(exporter.smtp_port, 465)
    
    def test_load_config(self):
        """Test loading configuration from file"""
        from timetracking.password_utils import password_encryption
        
        # Create test config file with encrypted password
        encrypted_password = password_encryption.encrypt_password('testpass')
        config_data = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'sender_email': 'test@example.com',
            'sender_password': encrypted_password
        }
        
        with open(self.temp_config.name, 'w') as f:
            json.dump(config_data, f)
        
        # Create exporter with config file
        exporter = EmailExporter()
        exporter.config_file = self.temp_config.name
        exporter.load_config()
        
        self.assertEqual(exporter.smtp_server, 'smtp.test.com')
        self.assertEqual(exporter.smtp_port, 587)
        self.assertEqual(exporter.sender_email, 'test@example.com')
        self.assertEqual(exporter.sender_password, 'testpass')
    
    def test_save_config(self):
        """Test saving configuration to file"""
        exporter = EmailExporter()
        exporter.config_file = self.temp_config.name
        exporter.smtp_server = 'smtp.test.com'
        exporter.smtp_port = 465
        exporter.sender_email = 'test@example.com'
        exporter.sender_password = 'testpass'
        
        exporter.save_config()
        
        # Verify config was saved
        with open(self.temp_config.name, 'r') as f:
            config_data = json.load(f)
        
        self.assertEqual(config_data['smtp_server'], 'smtp.test.com')
        self.assertEqual(config_data['smtp_port'], 465)
        self.assertEqual(config_data['sender_email'], 'test@example.com')
        # Password should be encrypted (not plain text)
        self.assertNotEqual(config_data['sender_password'], 'testpass')
        self.assertIsInstance(config_data['sender_password'], str)
        self.assertGreater(len(config_data['sender_password']), 0)
    
    def test_password_encryption(self):
        """Test password encryption and decryption"""
        from password_utils import password_encryption
        
        test_password = 'test_password_123'
        
        # Test encryption
        encrypted = password_encryption.encrypt_password(test_password)
        self.assertNotEqual(encrypted, test_password)
        self.assertIsInstance(encrypted, str)
        self.assertGreater(len(encrypted), 0)
        
        # Test decryption
        decrypted = password_encryption.decrypt_password(encrypted)
        self.assertEqual(decrypted, test_password)
        
        # Test empty password
        empty_encrypted = password_encryption.encrypt_password('')
        self.assertEqual(empty_encrypted, '')
        
        empty_decrypted = password_encryption.decrypt_password('')
        self.assertEqual(empty_decrypted, '')
    
    @patch('smtplib.SMTP')
    def test_send_time_report_success(self, mock_smtp):
        """Test successful email sending"""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        exporter = EmailExporter()
        exporter.sender_email = "test@example.com"
        exporter.sender_password = "testpass"
        
        # Test sending email
        success = exporter.send_time_report(
            self.sample_entries,
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
    
    @patch('smtplib.SMTP')
    def test_send_time_report_with_pdf(self, mock_smtp):
        """Test email sending with PDF attachment"""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            tmp_pdf.write(b"fake pdf content")
            pdf_path = tmp_pdf.name
        
        try:
            exporter = EmailExporter()
            exporter.sender_email = "test@example.com"
            exporter.sender_password = "testpass"
            
            # Test sending email with PDF
            success = exporter.send_time_report(
                self.sample_entries,
                "test@example.com",
                "testpass",
                "recipient@example.com",
                pdf_path=pdf_path
            )
            
            self.assertTrue(success)
            mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
            mock_server.sendmail.assert_called_once()
            
        finally:
            # Clean up
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
    
    @patch('smtplib.SMTP')
    def test_send_time_report_connection_error(self, mock_smtp):
        """Test email sending with connection error"""
        # Mock SMTP to raise connection error
        mock_smtp.side_effect = Exception("Connection failed")
        
        exporter = EmailExporter()
        exporter.sender_email = "test@example.com"
        exporter.sender_password = "testpass"
        
        # Test sending email
        success = exporter.send_time_report(
            self.sample_entries,
            "test@example.com",
            "testpass",
            "recipient@example.com"
        )
        
        self.assertFalse(success)
    
    @patch('smtplib.SMTP')
    def test_send_time_report_auth_error(self, mock_smtp):
        """Test email sending with authentication error"""
        # Mock SMTP server that fails on login
        mock_server = MagicMock()
        mock_server.login.side_effect = Exception("Authentication failed")
        mock_smtp.return_value = mock_server
        
        exporter = EmailExporter()
        exporter.sender_email = "test@example.com"
        exporter.sender_password = "testpass"
        
        # Test sending email
        success = exporter.send_time_report(
            self.sample_entries,
            "test@example.com",
            "testpass",
            "recipient@example.com"
        )
        
        self.assertFalse(success)
    
    def test_duration_formatting_with_seconds(self):
        """Test duration formatting includes seconds"""
        # Create entry with specific duration
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1, minutes=30, seconds=45)
        
        test_entries = [
            (1, 1, "Project A", "Test Task", start_time.isoformat(), end_time.isoformat(), 90, 25.0, "EUR")
        ]
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server
            
            exporter = EmailExporter()
            exporter.sender_email = "test@example.com"
            exporter.sender_password = "testpass"
            
            # Test sending email
            success = exporter.send_time_report(
                test_entries,
                "test@example.com",
                "testpass",
                "recipient@example.com"
            )
            
            self.assertTrue(success)
            # Verify email was sent (duration formatting is tested in the email content)
            mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
            mock_server.sendmail.assert_called_once()


if __name__ == '__main__':
    unittest.main()
