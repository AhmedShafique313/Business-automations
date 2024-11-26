import os
import json
import base64
from cryptography.fernet import Fernet
from pathlib import Path

class CredentialsManager:
    def __init__(self, credentials_file='credentials.json'):
        """Initialize credentials manager with encryption key and file path"""
        self.credentials_file = credentials_file
        self._init_encryption()
        self._load_credentials()

    def _init_encryption(self):
        """Initialize or load encryption key"""
        key_file = '.credentials.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.key)
        
        self.cipher = Fernet(self.key)

    def _load_credentials(self):
        """Load encrypted credentials from file"""
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
                if encrypted_data:
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    self.credentials = json.loads(decrypted_data)
                else:
                    self.credentials = {}
        else:
            self.credentials = {}

    def _save_credentials(self):
        """Save encrypted credentials to file"""
        encrypted_data = self.cipher.encrypt(json.dumps(self.credentials).encode())
        with open(self.credentials_file, 'wb') as f:
            f.write(encrypted_data)

    def set_credentials(self, service, credentials):
        """Set credentials for a service"""
        self.credentials[service] = credentials
        self._save_credentials()

    def get_credentials(self, service):
        """Get credentials for a service"""
        if service not in self.credentials:
            raise KeyError(f"No credentials found for {service}")
        return self.credentials[service]

    def remove_credentials(self, service):
        """Remove credentials for a service"""
        if service in self.credentials:
            del self.credentials[service]
            self._save_credentials()

    def list_services(self):
        """List all services with stored credentials"""
        return list(self.credentials.keys())

    def setup_twilio(self, account_sid, auth_token):
        """Set up Twilio credentials"""
        self.set_credentials('TWILIO', {
            'account_sid': account_sid,
            'auth_token': auth_token
        })

    def setup_smtp(self, server, username, password, port=587):
        """Set up SMTP credentials"""
        self.set_credentials('SMTP', {
            'server': server,
            'username': username,
            'password': password,
            'port': port
        })

    def setup_google(self, api_key, client_id, client_secret):
        """Set up Google API credentials"""
        self.set_credentials('GOOGLE', {
            'api_key': api_key,
            'client_id': client_id,
            'client_secret': client_secret
        })

    def setup_asana(self, access_token, workspace_id, team_id):
        """Set up Asana credentials"""
        self.set_credentials('ASANA', {
            'access_token': access_token,
            'workspace_id': workspace_id,
            'team_id': team_id
        })

    def validate_credentials(self, service):
        """Validate that all required credentials are present for a service"""
        required_fields = {
            'TWILIO': ['account_sid', 'auth_token'],
            'SMTP': ['server', 'username', 'password'],
            'GOOGLE': ['api_key', 'client_id', 'client_secret'],
            'ASANA': ['access_token', 'workspace_id', 'team_id']
        }
        
        if service not in required_fields:
            raise ValueError(f"Unknown service: {service}")
            
        if service not in self.credentials:
            return False
            
        creds = self.credentials[service]
        return all(field in creds for field in required_fields[service])

if __name__ == "__main__":
    # Example usage
    creds_manager = CredentialsManager()
    
    # Set up example credentials (replace with actual credentials)
    print("\n🔐 Setting up credentials...")
    
    # Twilio setup
    creds_manager.setup_twilio(
        account_sid=os.getenv('TWILIO_ACCOUNT_SID', 'your_account_sid'),
        auth_token=os.getenv('TWILIO_AUTH_TOKEN', 'your_auth_token')
    )
    
    # SMTP setup
    creds_manager.setup_smtp(
        server='smtp.gmail.com',
        username=os.getenv('SMTP_USERNAME', 'your_email@gmail.com'),
        password=os.getenv('SMTP_PASSWORD', 'your_app_password')
    )
    
    # Google API setup
    creds_manager.setup_google(
        api_key=os.getenv('GOOGLE_API_KEY', 'your_api_key'),
        client_id=os.getenv('GOOGLE_CLIENT_ID', 'your_client_id'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET', 'your_client_secret')
    )
    
    # Asana setup
    creds_manager.setup_asana(
        access_token=os.getenv('ASANA_ACCESS_TOKEN', 'your_access_token'),
        workspace_id=os.getenv('ASANA_WORKSPACE_ID', 'your_workspace_id'),
        team_id=os.getenv('ASANA_TEAM_ID', 'your_team_id')
    )
    
    # List available services
    print("\n📋 Available services:")
    for service in creds_manager.list_services():
        valid = creds_manager.validate_credentials(service)
        status = "✅" if valid else "❌"
        print(f"{status} {service}")
