import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
import aiohttp
from asana import Client as AsanaClient

class CommunicationTracker:
    def __init__(self, credentials_path: str = 'agents/credentials.json'):
        """Initialize Communication Tracker with Asana integration"""
        self.setup_logging()
        self.credentials_path = credentials_path
        with open(credentials_path) as f:
            self.credentials = json.load(f)['ASANA']
        
        # Get access token from credentials
        access_token = self.credentials['tokens']['access_token']
        if not access_token:
            print("No Asana access token found. Please follow these steps:")
            print("1. Go to https://app.asana.com/0/my-apps")
            print("2. Click on 'Manage Developer Apps'")
            print("3. Click 'New Access Token'")
            print("4. Add the token to credentials.json")
            sys.exit(1)
            
        # Format: 1/client_id:access_token
        formatted_token = f"1/{self.credentials['client_id']}:{access_token}"
        self.asana = AsanaClient.access_token(formatted_token)
        self.workspace_id = self.credentials['workspace_id']
        self.project = self._get_or_create_project()
        
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('communication_tracker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('CommunicationTracker')

    def _load_credentials(self, credentials_path: str) -> Dict:
        """Load Asana credentials from file"""
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                return creds['ASANA']
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            raise

    def _get_or_create_project(self) -> Dict:
        """Get or create the Real Estate Agent Outreach project"""
        projects = list(self.asana.projects.find_all({'workspace': self.workspace_id}))
        project = next(
            (p for p in projects if p['name'] == 'Real Estate Agent Outreach'),
            None
        )
        
        if not project:
            project = self.asana.projects.create_in_workspace(
                self.workspace_id,
                {'name': 'Real Estate Agent Outreach'}
            )
            
            # Create custom fields for tracking
            self.asana.custom_field_settings.create_for_project(
                project['gid'],
                {
                    'custom_field': {
                        'name': 'Status',
                        'type': 'enum',
                        'enum_options': [
                            {'name': 'New Lead'},
                            {'name': 'In Communication'},
                            {'name': 'Meeting Scheduled'},
                            {'name': 'Contract Sent'},
                            {'name': 'Client'},
                            {'name': 'Not Interested'}
                        ]
                    }
                }
            )
            
            self.asana.custom_field_settings.create_for_project(
                project['gid'],
                {
                    'custom_field': {
                        'name': 'Last Contact',
                        'type': 'date'
                    }
                }
            )
            
        return project

    def _get_or_create_agent_task(self, contact: Dict) -> str:
        """Get existing task for agent or create new one"""
        # Search for existing task by email
        tasks = list(self.asana.tasks.find_all({
            'project': self.project['gid'],
            'completed_since': 'now'  # Include incomplete tasks only
        }))
        
        task = next(
            (t for t in tasks if t['name'].startswith(f"[{contact['email']}]")),
            None
        )

        if task:
            # Update last contact date
            self.asana.tasks.update(
                task['gid'],
                {'custom_fields': {'Last Contact': datetime.now().strftime('%Y-%m-%d')}}
            )
            return task['gid']

        # Create new task if none exists
        task = self.asana.tasks.create_in_workspace(
            self.workspace_id,
            {
                'name': f"[{contact['email']}] {contact['name']} - {contact['location']}",
                'projects': [self.project['gid']],
                'notes': self._format_contact_notes(contact),
                'custom_fields': {
                    'Status': 'New Lead',
                    'Last Contact': datetime.now().strftime('%Y-%m-%d')
                }
            }
        )
        
        return task['gid']

    def _format_contact_notes(self, contact: Dict) -> str:
        """Format contact information for task notes"""
        return f"""
👤 Contact Information
---------------------
Name: {contact['name']}
Email: {contact['email']}
Location: {contact['location']}
Specialty: {contact.get('specialty', 'Real Estate Agent')}
Phone: {contact.get('phone', 'N/A')}

📝 Communication History
-----------------------
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Contact Created
"""

    def add_communication_note(self, task_id: str, channel: str, message_type: str, 
                             content: str, status: str = 'Sent') -> None:
        """Add a communication note to the contact's task"""
        task = self.asana.tasks.find_by_id(task_id)
        
        # Get existing notes
        notes = task['notes']
        
        # Add new communication entry
        new_entry = f"""
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {channel} {message_type}
Status: {status}
Content: {content}
---"""
        
        # Update task notes and status
        self.asana.tasks.update(
            task_id,
            {
                'notes': notes + new_entry,
                'custom_fields': {
                    'Status': 'In Communication',
                    'Last Contact': datetime.now().strftime('%Y-%m-%d')
                }
            }
        )

    async def track_whatsapp_message(self, contact: Dict, message_data: Dict, 
                                   status: str = 'Sent') -> None:
        """Track WhatsApp message in Asana"""
        task_id = self._get_or_create_agent_task(contact)
        
        if message_data['type'] == 'template':
            message_type = f"Template: {message_data['template_name']}"
            content = "Template message with parameters: " + \
                     ", ".join(message_data.get('parameters', []))
        else:
            message_type = "Message"
            content = message_data['text']
        
        self.add_communication_note(
            task_id=task_id,
            channel='WhatsApp',
            message_type=message_type,
            content=content,
            status=status
        )

    async def track_email_message(self, contact: Dict, message_data: Dict,
                                status: str = 'Sent') -> None:
        """Track email message in Asana"""
        task_id = self._get_or_create_agent_task(contact)
        
        self.add_communication_note(
            task_id=task_id,
            channel='Email',
            message_type=f"Subject: {message_data['subject']}",
            content=message_data['html_content'],
            status=status
        )

    async def track_response(self, contact: Dict, channel: str, content: str,
                           response_type: str = 'Reply') -> None:
        """Track a response received from the contact"""
        task_id = self._get_or_create_agent_task(contact)
        
        self.add_communication_note(
            task_id=task_id,
            channel=channel,
            message_type=f"Received {response_type}",
            content=content,
            status='Received'
        )

async def main():
    # Example usage
    tracker = CommunicationTracker()
    
    # Example contact
    contact = {
        'name': 'John Smith',
        'email': 'john@example.com',
        'location': 'Beverly Hills',
        'specialty': 'Luxury Real Estate',
        'phone': '+1 555-123-4567'
    }
    
    # Example WhatsApp message
    whatsapp_message = {
        'type': 'template',
        'template_name': 'design_gaga_intro',
        'parameters': [
            'John Smith',
            'Beverly Hills'
        ]
    }
    
    # Example email message
    email_message = {
        'subject': 'Enhance Your Beverly Hills Listings with Professional Home Staging',
        'html_content': 'Hello John, ...'
    }
    
    # Track outgoing communications
    await tracker.track_whatsapp_message(contact, whatsapp_message)
    await tracker.track_email_message(contact, email_message)
    
    # Example: Track a response
    await tracker.track_response(
        contact,
        'WhatsApp',
        'Thanks for reaching out! I would love to learn more about your services.'
    )

if __name__ == "__main__":
    asyncio.run(main())
