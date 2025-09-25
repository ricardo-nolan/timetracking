"""
Comprehensive password utilities tests to improve coverage
"""
import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timetracking.password_utils import PasswordEncryption


class TestPasswordEncryptionComprehensive(unittest.TestCase):
    """Comprehensive test cases for password encryption functionality"""
    
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
    
    def test_encrypt_decrypt_complex_passwords(self):
        """Test encryption/decryption of complex passwords"""
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        complex_passwords = [
            "P@ssw0rd!123",
            "VeryLongPasswordWithSpecialChars!@#$%^&*()",
            "Password with spaces and numbers 123",
            "Unicode: émojis 🚀 and spëcial chars",
            "Password\nwith\nnewlines",
            "Password\twith\ttabs",
            "Password with 'quotes' and \"double quotes\"",
        ]
        
        for password in complex_passwords:
            encrypted = encryption.encrypt_password(password)
            decrypted = encryption.decrypt_password(encrypted)
            
            self.assertNotEqual(password, encrypted)
            self.assertEqual(password, decrypted)
    
    def test_encrypt_decrypt_very_long_passwords(self):
        """Test encryption/decryption of very long passwords"""
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        # Very long password (1000 characters)
        long_password = "A" * 1000
        
        encrypted = encryption.encrypt_password(long_password)
        decrypted = encryption.decrypt_password(encrypted)
        
        self.assertNotEqual(long_password, encrypted)
        self.assertEqual(long_password, decrypted)
    
    def test_encrypt_decrypt_binary_data(self):
        """Test encryption/decryption of binary-like data"""
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        binary_like_passwords = [
            "Password\x00with\x00nulls",
            "Password\x01\x02\x03\x04",
            "Password\xFF\xFE\xFD\xFC",
        ]
        
        for password in binary_like_passwords:
            encrypted = encryption.encrypt_password(password)
            decrypted = encryption.decrypt_password(encrypted)
            
            self.assertNotEqual(password, encrypted)
            self.assertEqual(password, decrypted)
    
    def test_key_file_creation_and_loading(self):
        """Test key file creation and loading"""
        # Remove existing key file
        if os.path.exists(self.temp_key_file.name):
            os.unlink(self.temp_key_file.name)
        
        # Create new encryption instance (should create key file)
        encryption1 = PasswordEncryption(self.temp_key_file.name)
        
        # Verify key file was created
        self.assertTrue(os.path.exists(self.temp_key_file.name))
        self.assertGreater(os.path.getsize(self.temp_key_file.name), 0)
        
        # Test that key file can be loaded
        encryption2 = PasswordEncryption(self.temp_key_file.name)
        
        # Both instances should be able to encrypt/decrypt
        password = "test_password"
        encrypted1 = encryption1.encrypt_password(password)
        encrypted2 = encryption2.encrypt_password(password)
        
        # Both should produce different encrypted values (due to salt)
        self.assertNotEqual(encrypted1, encrypted2)
        
        # But both should decrypt to same value
        decrypted1 = encryption1.decrypt_password(encrypted1)
        decrypted2 = encryption2.decrypt_password(encrypted2)
        
        self.assertEqual(decrypted1, password)
        self.assertEqual(decrypted2, password)
    
    def test_key_file_corruption_handling(self):
        """Test handling of corrupted key file"""
        # Create corrupted key file
        with open(self.temp_key_file.name, 'wb') as f:
            f.write(b"corrupted_key_data")
        
        # Should handle corrupted key gracefully
        with self.assertRaises(ValueError):
            encryption = PasswordEncryption(self.temp_key_file.name)
    
    def test_key_file_permissions(self):
        """Test key file permissions handling"""
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        # Test that key file is readable
        self.assertTrue(os.access(self.temp_key_file.name, os.R_OK))
        
        # Test that key file is writable
        self.assertTrue(os.access(self.temp_key_file.name, os.W_OK))
    
    def test_encryption_consistency(self):
        """Test encryption consistency across multiple instances"""
        encryption1 = PasswordEncryption(self.temp_key_file.name)
        encryption2 = PasswordEncryption(self.temp_key_file.name)
        
        password = "consistent_password"
        
        # Both instances should be able to encrypt/decrypt
        encrypted1 = encryption1.encrypt_password(password)
        encrypted2 = encryption2.encrypt_password(password)
        
        # Both should produce different encrypted values (due to salt)
        self.assertNotEqual(encrypted1, encrypted2)
        
        # But both should decrypt to same value
        decrypted1 = encryption1.decrypt_password(encrypted1)
        decrypted2 = encryption2.decrypt_password(encrypted2)
        
        self.assertEqual(decrypted1, password)
        self.assertEqual(decrypted2, password)
    
    def test_encryption_with_different_key_files(self):
        """Test encryption with different key files"""
        # Create second key file
        temp_key_file2 = tempfile.NamedTemporaryFile(delete=False)
        temp_key_file2.close()
        
        try:
            encryption1 = PasswordEncryption(self.temp_key_file.name)
            encryption2 = PasswordEncryption(temp_key_file2.name)
            
            password = "test_password"
            
            # Encrypt with different key files
            encrypted1 = encryption1.encrypt_password(password)
            encrypted2 = encryption2.encrypt_password(password)
            
            # Should produce different encrypted values
            self.assertNotEqual(encrypted1, encrypted2)
            
            # Each should only decrypt with its own key
            decrypted1 = encryption1.decrypt_password(encrypted1)
            decrypted2 = encryption2.decrypt_password(encrypted2)
            
            self.assertEqual(decrypted1, password)
            self.assertEqual(decrypted2, password)
            
            # Cross-decryption should fail
            with self.assertRaises(Exception):
                encryption1.decrypt_password(encrypted2)
            
            with self.assertRaises(Exception):
                encryption2.decrypt_password(encrypted1)
        finally:
            if os.path.exists(temp_key_file2.name):
                os.unlink(temp_key_file2.name)
    
    def test_encryption_with_missing_key_file(self):
        """Test encryption with missing key file"""
        # Remove key file
        if os.path.exists(self.temp_key_file.name):
            os.unlink(self.temp_key_file.name)
        
        # Should create new key file
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        # Verify key file was created
        self.assertTrue(os.path.exists(self.temp_key_file.name))
        
        # Should be able to encrypt/decrypt
        password = "test_password"
        encrypted = encryption.encrypt_password(password)
        decrypted = encryption.decrypt_password(encrypted)
        
        self.assertEqual(decrypted, password)
    
    def test_encryption_with_readonly_key_file(self):
        """Test encryption with readonly key file"""
        # Make key file readonly
        os.chmod(self.temp_key_file.name, 0o444)
        
        try:
            # Should still work for reading
            encryption = PasswordEncryption(self.temp_key_file.name)
            
            password = "test_password"
            encrypted = encryption.encrypt_password(password)
            decrypted = encryption.decrypt_password(encrypted)
            
            self.assertEqual(decrypted, password)
        finally:
            # Restore write permissions
            os.chmod(self.temp_key_file.name, 0o644)
    
    def test_encryption_with_empty_key_file(self):
        """Test encryption with empty key file"""
        # Create empty key file
        with open(self.temp_key_file.name, 'wb') as f:
            f.write(b"")
        
        # Should handle empty key file by regenerating a valid key
        encryption = PasswordEncryption(self.temp_key_file.name)
        password = "test_password"
        encrypted = encryption.encrypt_password(password)
        decrypted = encryption.decrypt_password(encrypted)
        self.assertEqual(decrypted, password)
    
    def test_encryption_with_short_key_file(self):
        """Test encryption with short key file"""
        # Create short key file
        with open(self.temp_key_file.name, 'wb') as f:
            f.write(b"short")
        
        # Should handle short key file gracefully
        with self.assertRaises(ValueError):
            encryption = PasswordEncryption(self.temp_key_file.name)
    
    def test_encryption_with_invalid_key_file(self):
        """Test encryption with invalid key file"""
        # Create invalid key file
        with open(self.temp_key_file.name, 'wb') as f:
            f.write(b"invalid_key_data_that_is_not_base64_encoded")
        
        # Should handle invalid key file gracefully
        with self.assertRaises(ValueError):
            encryption = PasswordEncryption(self.temp_key_file.name)
    
    def test_encryption_with_unicode_passwords(self):
        """Test encryption with unicode passwords"""
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        unicode_passwords = [
            "密码123",
            "пароль456",
            "كلمة المرور789",
            "パスワード012",
            "סיסמה345",
            "كلمة السر678",
            "รหัสผ่าน901",
            "كلمة المرور234",
            "סיסמה567",
            "كلمة السر890",
        ]
        
        for password in unicode_passwords:
            encrypted = encryption.encrypt_password(password)
            decrypted = encryption.decrypt_password(encrypted)
            
            self.assertNotEqual(password, encrypted)
            self.assertEqual(password, decrypted)
    
    def test_encryption_with_special_characters(self):
        """Test encryption with special characters"""
        encryption = PasswordEncryption(self.temp_key_file.name)
        
        special_char_passwords = [
            "!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "`~!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "Password with spaces",
            "Password\twith\ttabs",
            "Password\nwith\nnewlines",
            "Password with 'quotes'",
            "Password with \"double quotes\"",
            "Password with `backticks`",
            "Password with $dollar$ signs",
            "Password with %percent% signs",
        ]
        
        for password in special_char_passwords:
            encrypted = encryption.encrypt_password(password)
            decrypted = encryption.decrypt_password(encrypted)
            
            self.assertNotEqual(password, encrypted)
            self.assertEqual(password, decrypted)


if __name__ == '__main__':
    unittest.main()
