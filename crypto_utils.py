
from cryptography.fernet import Fernet
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import streamlit as st

class CryptoUtils:
    def __init__(self):
        # Get or generate encryption key
        if 'crypto_key' not in st.session_state:
            st.session_state.crypto_key = self._get_or_generate_key()
        self.fernet = Fernet(st.session_state.crypto_key)
    
    def _get_or_generate_key(self):
        """Get key from environment or generate new one"""
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            # Generate a key from password
            password = os.getenv('ENCRYPTION_PASSWORD', 'default-password').encode()
            salt = os.getenv('ENCRYPTION_SALT', 'default-salt').encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt string data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt encrypted string data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt dictionary values"""
        return {k: self.encrypt_data(str(v)) for k, v in data.items()}
    
    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """Decrypt dictionary values"""
        return {k: self.decrypt_data(v) for k, v in encrypted_data.items()}
