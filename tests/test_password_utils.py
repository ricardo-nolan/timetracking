"""
Unit tests for password encryption utilities
"""
import unittest
import tempfile
import os
import sys
from unittest.mock import patch
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timetracking.password_utils import PasswordEncryption


class TestPasswordEncryption(unittest.TestCase):
    """Test cases for PasswordEncryption class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_key_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_key_file.close()
        
        # Create a valid key file for testing
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        with open(self.temp_key_file.name, 'wb') as f:
            f.write(key)
        
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.temp_key_file.name):
            os.unlink(self.temp_key_file.name)
    
    def test_encrypt_decrypt_password(self):
        """Test password encryption and decryption"""
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        # Test normal password
        password = "test_password_123"
        encrypted = encryption.encrypt_password(password)
        decrypted = encryption.decrypt_password(encrypted)
        
        self.assertNotEqual(password, encrypted)
        self.assertEqual(password, decrypted)
    
    def test_encrypt_empty_password(self):
        """Test encryption of empty password"""
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        encrypted = encryption.encrypt_password("")
        decrypted = encryption.decrypt_password(encrypted)
        
        self.assertEqual("", decrypted)
    
    def test_decrypt_empty_password(self):
        """Test decryption of empty password"""
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        decrypted = encryption.decrypt_password("")
        
        self.assertEqual("", decrypted)
    
    def test_key_file_creation(self):
        """Test that key file is created if it doesn't exist"""
        if os.path.exists(self.temp_key_file.name):
            os.unlink(self.temp_key_file.name)
        
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        self.assertTrue(os.path.exists(self.temp_key_file.name))
        self.assertGreater(os.path.getsize(self.temp_key_file.name), 0)
    
    def test_key_file_loading(self):
        """Test that existing key file is loaded"""
        encryption1 = PasswordEncryption(self.temp_key_file.name)
        password = "test_password"
        encrypted1 = encryption1.encrypt_password(password)
        
        # Create new instance with same key file
        encryption2 = PasswordEncryption(self.temp_key_file.name)
        decrypted = encryption2.decrypt_password(encrypted1)
        
        self.assertEqual(password, decrypted)
    
    def test_different_passwords_different_encryption(self):
        """Test that different passwords produce different encrypted values"""
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        password1 = "password1"
        password2 = "password2"
        
        encrypted1 = encryption.encrypt_password(password1)
        encrypted2 = encryption.encrypt_password(password2)
        
        self.assertNotEqual(encrypted1, encrypted2)
    
    def test_same_password_different_encryption(self):
        """Test that same password produces different encrypted values (due to salt)"""
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        password = "same_password"
        
        encrypted1 = encryption.encrypt_password(password)
        encrypted2 = encryption.encrypt_password(password)
        
        # Should be different due to random salt
        self.assertNotEqual(encrypted1, encrypted2)
        
        # But both should decrypt to same value
        decrypted1 = encryption.decrypt_password(encrypted1)
        decrypted2 = encryption.decrypt_password(encrypted2)
        
        self.assertEqual(decrypted1, decrypted2)
        self.assertEqual(password, decrypted1)


if __name__ == '__main__':
    unittest.main()
