import os
from typing import Dict, Optional
from google.oauth2.credentials import Credentials
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from instagram_private_api import Client as InstagramAPI
from linkedin_api import Linkedin
from mailchimp_marketing import Client as MailchimpClient
from hubspot import HubSpot

class APIAuthenticator:
    """Handles authentication for various API services."""
    
    def __init__(self):
        """Initialize API authenticator with credentials from environment variables."""
        self.credentials = {}
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from environment variables."""
        # Google Analytics credentials
        self.credentials['google'] = {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN')
        }
        
        # Facebook credentials
        self.credentials['facebook'] = {
            'access_token': os.getenv('FACEBOOK_ACCESS_TOKEN')
        }
        
        # Instagram credentials
        self.credentials['instagram'] = {
            'username': os.getenv('INSTAGRAM_USERNAME'),
            'password': os.getenv('INSTAGRAM_PASSWORD')
        }
        
        # LinkedIn credentials
        self.credentials['linkedin'] = {
            'username': os.getenv('LINKEDIN_USERNAME'),
            'password': os.getenv('LINKEDIN_PASSWORD')
        }
        
        # MailChimp credentials
        self.credentials['mailchimp'] = {
            'api_key': os.getenv('MAILCHIMP_API_KEY')
        }
        
        # HubSpot credentials
        self.credentials['hubspot'] = {
            'api_key': os.getenv('HUBSPOT_API_KEY')
        }
    
    def get_google_analytics_client(self) -> Optional[Credentials]:
        """Get authenticated Google Analytics client."""
        creds = self.credentials['google']
        if all(creds.values()):
            return Credentials.from_authorized_user_info(creds)
        return None
    
    def get_facebook_client(self) -> Optional[FacebookAdsApi]:
        """Get authenticated Facebook client."""
        access_token = self.credentials['facebook']['access_token']
        if access_token:
            return FacebookAdsApi.init(access_token=access_token)
        return None
    
    def get_instagram_client(self) -> Optional[InstagramAPI]:
        """Get authenticated Instagram client."""
        creds = self.credentials['instagram']
        if all(creds.values()):
            return InstagramAPI(
                username=creds['username'],
                password=creds['password']
            )
        return None
    
    def get_linkedin_client(self) -> Optional[Linkedin]:
        """Get authenticated LinkedIn client."""
        creds = self.credentials['linkedin']
        if all(creds.values()):
            return Linkedin(
                username=creds['username'],
                password=creds['password']
            )
        return None
    
    def get_mailchimp_client(self) -> Optional[MailchimpClient]:
        """Get authenticated MailChimp client."""
        api_key = self.credentials['mailchimp']['api_key']
        if api_key:
            client = MailchimpClient()
            client.set_config({
                "api_key": api_key,
                "server": api_key.split('-')[-1]
            })
            return client
        return None
    
    def get_hubspot_client(self) -> Optional[HubSpot]:
        """Get authenticated HubSpot client."""
        api_key = self.credentials['hubspot']['api_key']
        if api_key:
            return HubSpot(api_key=api_key)
        return None
