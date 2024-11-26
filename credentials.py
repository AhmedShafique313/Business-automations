"""Credentials management module for secure storage and retrieval of API keys and passwords."""

from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
import base64
import json
from typing import Optional, Dict, Any

class CredentialsManager:
    def __init__(self):
        """Initialize credentials manager with encryption and environment variables."""
        # Load environment variables
        load_dotenv()
        
        # Generate or load encryption key
        self.key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.key)
        
        # Load credentials from environment variables
        self.env_credentials = {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'asana_access_token': os.getenv('ASANA_ACCESS_TOKEN'),
            'sendgrid_api_key': os.getenv('SENDGRID_API_KEY'),
            'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'clearbit_api_key': os.getenv('CLEARBIT_API_KEY'),
            'facebook_access_token': os.getenv('FACEBOOK_ACCESS_TOKEN'),
            'instagram_access_token': os.getenv('INSTAGRAM_ACCESS_TOKEN'),
            'linkedin_access_token': os.getenv('LINKEDIN_ACCESS_TOKEN')
        }
        
        # Load encrypted credentials
        self.encrypted_credentials = self._load_encrypted_credentials()
    
    def _get_or_create_key(self) -> bytes:
        """Get existing encryption key or create a new one."""
        key_file = '.credential.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def _encrypt(self, value: str) -> str:
        """Encrypt a value."""
        return self.cipher_suite.encrypt(value.encode()).decode()

    def _decrypt(self, encrypted_value: str) -> str:
        """Decrypt a value."""
        return self.cipher_suite.decrypt(encrypted_value.encode()).decode()
    
    def _load_encrypted_credentials(self) -> Dict[str, Any]:
        """Load encrypted credentials from file."""
        creds_file = 'credentials.json'
        if os.path.exists(creds_file):
            with open(creds_file, 'r') as f:
                return json.load(f)
        return {}

    def get_credential(self, key: str) -> Optional[str]:
        """Get a credential by key, checking environment variables first."""
        # Check environment variables first
        if key in self.env_credentials and self.env_credentials[key]:
            return self.env_credentials[key]
        
        # Then check encrypted credentials
        if key in self.encrypted_credentials:
            creds = self.encrypted_credentials[key]
            if isinstance(creds, dict) and 'password' in creds:
                return self._decrypt(creds['password'])
            elif isinstance(creds, str):
                return self._decrypt(creds)
        
        return None

    def set_credential(self, key: str, value: str, encrypt: bool = True) -> None:
        """Set a credential, optionally encrypting it."""
        if encrypt:
            self.encrypted_credentials[key] = self._encrypt(value)
        else:
            self.env_credentials[key] = value

    def get_service_credentials(self, service: str) -> Dict[str, str]:
        """Get all credentials for a specific service."""
        if service in self.encrypted_credentials:
            creds = self.encrypted_credentials[service].copy()
            if 'password' in creds:
                creds['password'] = self._decrypt(creds['password'])
            return creds
        return {}

# Example usage:
if __name__ == "__main__":
    # Initialize credentials manager
    creds_manager = CredentialsManager()
    
    # Example: Get Instagram credentials
    instagram_creds = creds_manager.get_service_credentials('INSTAGRAM')
    print(f"Instagram Username: {instagram_creds.get('username')}")
    # Password is securely decrypted only when needed
    # print(f"Instagram Password: {instagram_creds.get('password')}")
