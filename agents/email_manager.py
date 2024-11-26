import os
from mailjet_rest import Client
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailManager:
    def __init__(self, credentials_file: str):
        """Initialize EmailManager with Mailjet credentials."""
        with open(credentials_file) as f:
            credentials = json.load(f)
            
        mailjet_creds = credentials.get('MAILJET', {})
        self.api_key = mailjet_creds.get('api_key')
        self.api_secret = mailjet_creds.get('api_secret')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Mailjet API key and secret are required")
            
        self.client = Client(auth=(self.api_key, self.api_secret))
        
    async def send_personalized_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        template_id: Optional[int] = None,
        template_variables: Optional[Dict] = None
    ) -> Dict:
        """Send a personalized email using Mailjet."""
        try:
            data = {
                'Messages': [
                    {
                        'From': {
                            'Email': "your-verified-sender@domain.com",
                            'Name': "Your Name"
                        },
                        'To': [
                            {
                                'Email': to_email,
                                'Name': to_name
                            }
                        ],
                        'Subject': subject,
                        'HTMLPart': html_content
                    }
                ]
            }
            
            # If using a template
            if template_id and template_variables:
                data['Messages'][0]['TemplateID'] = template_id
                data['Messages'][0]['TemplateLanguage'] = True
                data['Messages'][0]['Variables'] = template_variables
            
            result = self.client.send.create(data=data)
            
            if result.status_code == 200:
                logger.info(f"Email sent successfully to {to_email}")
                return result.json()
            else:
                logger.error(f"Failed to send email: {result.json()}")
                raise Exception(f"Failed to send email: {result.json()}")
                
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise
            
    async def create_template(
        self,
        name: str,
        subject: str,
        html_content: str
    ) -> Dict:
        """Create an email template in Mailjet."""
        try:
            data = {
                'Name': name,
                'Subject': subject,
                'HTMLPart': html_content
            }
            
            result = self.client.template.create(data=data)
            
            if result.status_code == 201:
                logger.info(f"Template created successfully: {name}")
                return result.json()
            else:
                logger.error(f"Failed to create template: {result.json()}")
                raise Exception(f"Failed to create template: {result.json()}")
                
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            raise
            
    async def track_email_engagement(self, message_id: str) -> Dict:
        """Track email engagement metrics using Mailjet's API."""
        try:
            result = self.client.messagesentstatistics.get(id=message_id)
            
            if result.status_code == 200:
                stats = result.json()
                logger.info(f"Retrieved engagement stats for message {message_id}")
                return stats
            else:
                logger.error(f"Failed to get engagement stats: {result.json()}")
                raise Exception(f"Failed to get engagement stats: {result.json()}")
                
        except Exception as e:
            logger.error(f"Error tracking engagement: {str(e)}")
            raise
            
    async def schedule_follow_up(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        send_at: datetime
    ) -> Dict:
        """Schedule a follow-up email for future delivery."""
        try:
            data = {
                'Messages': [
                    {
                        'From': {
                            'Email': "your-verified-sender@domain.com",
                            'Name': "Your Name"
                        },
                        'To': [
                            {
                                'Email': to_email,
                                'Name': to_name
                            }
                        ],
                        'Subject': subject,
                        'HTMLPart': html_content,
                        'ScheduledAt': send_at.isoformat()
                    }
                ]
            }
            
            result = self.client.send.create(data=data)
            
            if result.status_code == 200:
                logger.info(f"Follow-up email scheduled for {to_email} at {send_at}")
                return result.json()
            else:
                logger.error(f"Failed to schedule follow-up: {result.json()}")
                raise Exception(f"Failed to schedule follow-up: {result.json()}")
                
        except Exception as e:
            logger.error(f"Error scheduling follow-up: {str(e)}")
            raise
