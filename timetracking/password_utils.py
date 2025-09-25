"""
Password encryption utilities for secure storage of email passwords
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class PasswordEncryption:
    """Handle password encryption and decryption"""
    
    def __init__(self, key_file: str = None):
        if key_file is None:
            # Use user's home directory for key file
            home_dir = os.path.expanduser("~")
            self.key_file = os.path.join(home_dir, "email_key.key")
        else:
            self.key_file = key_file
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)

    def _get_or_create_key(self) -> bytes:
        """Get existing key or create a new one"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                data = f.read()
            # Enforce valid Fernet key format
            if not data:
                # If file exists but empty (new temp file), generate key
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                return key
            try:
                # This will raise if invalid
                Fernet(data)
            except Exception as exc:
                raise ValueError("Invalid Fernet key file") from exc
            return data
        # Create a new key (or regenerate due to failure above)
        key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(key)
        return key
    
    def encrypt_password(self, password: str) -> str:
        """Encrypt a password"""
        if not password:
            return ""
        
        # Convert string to bytes and encrypt
        encrypted_bytes = self.cipher.encrypt(password.encode())
        # Convert to base64 string for JSON storage
        return base64.b64encode(encrypted_bytes).decode()
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a password"""
        if not encrypted_password:
            return ""
        
        try:
            # Convert from base64 and decrypt
            encrypted_bytes = base64.b64decode(encrypted_password.encode())
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception:
            # If decryption fails, raise to surface misuse (e.g., wrong key)
            raise
    
    def is_encrypted(self, password: str) -> bool:
        """Check if a password appears to be encrypted (base64 format)"""
        if not password:
            return False
        
        try:
            # Try to decode as base64
            base64.b64decode(password.encode())
            return True
        except Exception:
            return False


# Global instance for use throughout the application
password_encryption = PasswordEncryption()
