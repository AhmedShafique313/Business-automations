import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleService:
    """Service for interacting with Google APIs"""
    
    def __init__(self):
        credentials_path = Path(__file__).parent.parent.parent.parent / 'credentials.json'
        with open(credentials_path) as f:
            self.credentials = json.load(f)
        
        self.gmb_endpoint = self.credentials['GOOGLE']['GMB_API']['performance_endpoint']
        self.project_id = self.credentials['GOOGLE']['OAUTH']['project_id']
        
    def _get_credentials(self, token_info: Dict[str, Any]) -> Optional[Credentials]:
        """Get OAuth2 credentials from token info"""
        try:
            return Credentials(
                token=token_info.get('access_token'),
                refresh_token=token_info.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.credentials['GOOGLE']['OAUTH']['client_id'],
                client_secret=self.credentials['GOOGLE']['OAUTH']['client_secret']
            )
        except Exception as e:
            logger.error(f"Error creating credentials: {str(e)}")
            return None
            
    async def get_business_info(self, business_id: str, token_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get Google My Business information"""
        try:
            credentials = self._get_credentials(token_info)
            if not credentials:
                return None
                
            service = build(
                'mybusinessbusinessinformation', 
                'v1', 
                credentials=credentials
            )
            
            result = service.accounts().locations().get(
                name=f"locations/{business_id}"
            ).execute()
            
            return result
            
        except HttpError as e:
            logger.error(f"HTTP error getting business info: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting business info: {str(e)}")
            return None
            
    async def get_business_metrics(
        self, 
        business_id: str,
        token_info: Dict[str, Any],
        metric_requests: Optional[list] = None
    ) -> Optional[Dict[str, Any]]:
        """Get Google My Business metrics"""
        try:
            credentials = self._get_credentials(token_info)
            if not credentials:
                return None
                
            service = build(
                'mybusinessperformance',
                'v1',
                credentials=credentials
            )
            
            if not metric_requests:
                metric_requests = [
                    "QUERIES_DIRECT",
                    "QUERIES_INDIRECT",
                    "VIEWS_MAPS",
                    "VIEWS_SEARCH",
                    "ACTIONS_WEBSITE",
                    "ACTIONS_PHONE",
                    "ACTIONS_DRIVING_DIRECTIONS"
                ]
            
            body = {
                "locationNames": [f"locations/{business_id}"],
                "basicRequest": {
                    "metricRequests": [
                        {"metric": metric} for metric in metric_requests
                    ],
                    "timeRange": {
                        "options": "LAST_30_DAYS"
                    }
                }
            }
            
            result = service.locations().fetchMetricsReport(
                name=f"locations/{business_id}",
                body=body
            ).execute()
            
            return result
            
        except HttpError as e:
            logger.error(f"HTTP error getting business metrics: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting business metrics: {str(e)}")
            return None
