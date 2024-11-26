"""
Authentication Manager
Handles all authentication flows for external services.
"""

import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import base64
from pathlib import Path

import jwt
from oauthlib.oauth2 import WebApplicationClient
import requests
from requests.auth import HTTPBasicAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auth.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AuthManager:
    """Manages authentication for all external services."""
    
    def __init__(self):
        """Initialize the auth manager."""
        # Set up token storage directory
        self.token_dir = Path(__file__).parent / 'tokens'
        self.token_dir.mkdir(exist_ok=True)
        
        # Load OAuth configs
        self.configs = self._load_oauth_configs()
        
        # Initialize OAuth clients only for services with client_id
        self.clients = {}
        for service, config in self.configs.items():
            if config.get('client_id'):
                self.clients[service] = WebApplicationClient(config['client_id'])
    
    def _load_oauth_configs(self) -> Dict:
        """Load OAuth configurations from environment or config file."""
        try:
            # First try environment variables
            configs = {}
            services = ['asana', 'google', 'facebook', 'linkedin']
            
            for service in services:
                client_id = os.getenv(f'{service.upper()}_CLIENT_ID')
                client_secret = os.getenv(f'{service.upper()}_CLIENT_SECRET')
                
                if client_id and client_secret:
                    configs[service] = {
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'auth_url': os.getenv(f'{service.upper()}_AUTH_URL'),
                        'token_url': os.getenv(f'{service.upper()}_TOKEN_URL'),
                        'redirect_uri': os.getenv(f'{service.upper()}_REDIRECT_URI')
                    }
            
            # If no configs in env, try config file
            if not configs:
                config_path = Path(__file__).parent / 'oauth_config.json'
                if config_path.exists():
                    with open(config_path) as f:
                        configs = json.load(f)
                        
                        # Convert to expected format if using old format
                        if not isinstance(configs.get('asana', {}), dict):
                            configs = {
                                'asana': {
                                    'access_token': configs.get('ASANA_ACCESS_TOKEN'),
                                    'client_id': '',
                                    'client_secret': '',
                                    'auth_url': '',
                                    'token_url': '',
                                    'redirect_uri': ''
                                }
                            }
            
            return configs
            
        except Exception as e:
            logger.error(f"Failed to load OAuth configs: {str(e)}")
            raise
    
    def get_authorization_url(self, service: str, state: Optional[str] = None) -> str:
        """Get the authorization URL for a service."""
        try:
            if service not in self.configs:
                raise ValueError(f"Service {service} not configured")
            
            config = self.configs[service]
            client = self.clients.get(service)
            
            if not client:
                raise ValueError(f"Service {service} not configured with client ID")
            
            # Generate authorization URL
            auth_url = client.prepare_request_uri(
                config['auth_url'],
                redirect_uri=config['redirect_uri'],
                scope=['basic_access'],  # Customize based on service
                state=state
            )
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Failed to get authorization URL for {service}: {str(e)}")
            raise
    
    async def exchange_code_for_token(
        self,
        service: str,
        code: str,
        state: Optional[str] = None
    ) -> Dict:
        """Exchange authorization code for access token."""
        try:
            if service not in self.configs:
                raise ValueError(f"Service {service} not configured")
            
            config = self.configs[service]
            client = self.clients.get(service)
            
            if not client:
                raise ValueError(f"Service {service} not configured with client ID")
            
            # Prepare token request
            token_url = config['token_url']
            auth = HTTPBasicAuth(config['client_id'], config['client_secret'])
            
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': config['redirect_uri']
            }
            
            # Make token request
            response = requests.post(
                token_url,
                auth=auth,
                data=data,
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise ValueError(f"Failed to exchange code for token: {response.status_code}")
            
            token_data = response.json()
            
            # Store token in file
            await self._store_token(service, token_data)
            
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {str(e)}")
            raise
    
    async def refresh_token(self, service: str) -> Dict:
        """Refresh the access token for a service."""
        try:
            if service not in self.configs:
                raise ValueError(f"Service {service} not configured")
            
            # Get refresh token from file
            token_data = self._load_token_data(service)
            if not token_data or 'refresh_token' not in token_data:
                raise ValueError(f"No refresh token found for {service}")
            
            config = self.configs[service]
            
            # Prepare refresh request
            auth = HTTPBasicAuth(config['client_id'], config['client_secret'])
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': token_data['refresh_token']
            }
            
            # Make refresh request
            response = requests.post(
                config['token_url'],
                auth=auth,
                data=data,
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                raise ValueError(f"Failed to refresh token: {response.status_code}")
            
            new_token_data = response.json()
            
            # Store new token
            await self._store_token(service, new_token_data)
            
            return new_token_data
            
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            raise
    
    async def get_valid_token(self, service: str) -> str:
        """Get a valid access token, refreshing if necessary."""
        try:
            # Get token data from file
            token_data = self._load_token_data(service)
            
            if not token_data:
                raise ValueError(f"No token found for {service}")
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if expires_at <= datetime.now() + timedelta(minutes=5):
                # Refresh token
                token_data = await self.refresh_token(service)
            
            return token_data['access_token']
            
        except Exception as e:
            logger.error(f"Failed to get valid token: {str(e)}")
            raise
    
    async def _store_token(self, service: str, token_data: Dict):
        """Store token data in file."""
        try:
            # Calculate expiration
            expires_in = token_data.get('expires_in', 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Prepare data for storage
            storage_data = {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', ''),
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_at': expires_at.isoformat(),
                'scope': token_data.get('scope', '')
            }
            
            # Store in file
            token_file = self.token_dir / f'{service}_token.json'
            with open(token_file, 'w') as f:
                json.dump(storage_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to store token: {str(e)}")
            raise
    
    def _load_token_data(self, service: str) -> Optional[Dict]:
        """Load token data from file."""
        try:
            token_file = self.token_dir / f'{service}_token.json'
            if not token_file.exists():
                return None
                
            with open(token_file) as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to load token data: {str(e)}")
            return None
    
    def get_asana_token(self) -> str:
        """Get a valid Asana token, refreshing if necessary."""
        try:
            # First try to load existing token
            token_path = self.token_dir / 'asana_token.json'
            if token_path.exists():
                with open(token_path) as f:
                    token_data = json.load(f)
                    expires_at = datetime.fromtimestamp(token_data['expires_at'])
                    
                    # Check if token is still valid
                    if datetime.now() < expires_at:
                        return token_data['access_token']
                    
                    # Try to refresh token
                    if 'refresh_token' in token_data:
                        new_token = self.refresh_token('asana')
                        if new_token:
                            return new_token['access_token']
            
            # If no valid token found, use PAT from config
            config_path = Path(__file__).parent / 'oauth_config.json'
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                    if 'asana' in config and 'access_token' in config['asana']:
                        return config['asana']['access_token']
            
            raise ValueError("No valid Asana token found")
            
        except Exception as e:
            logger.error(f"Error getting Asana token: {str(e)}")
            raise
    
    def revoke_token(self, service: str):
        """Revoke tokens for a service."""
        try:
            # Delete token file
            token_file = self.token_dir / f'{service}_token.json'
            if token_file.exists():
                token_file.unlink()
            logger.info(f"Revoked tokens for {service}")
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {str(e)}")
            raise
