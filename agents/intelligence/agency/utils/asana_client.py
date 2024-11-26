"""
Asana Integration Client
Manages interactions with Asana for task and project management.
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asana
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsanaClient:
    """Client for interacting with Asana API."""
    
    def __init__(self):
        """Initialize the Asana client."""
        self.client = asana.Client.access_token(os.getenv('ASANA_ACCESS_TOKEN'))
        self.workspace_gid = os.getenv('ASANA_WORKSPACE_GID')
        self.project_gid = os.getenv('ASANA_PROJECT_GID')
        
        if not all([self.client, self.workspace_gid, self.project_gid]):
            raise ValueError("Missing required Asana configuration. Please check environment variables.")
            
        # Set up default headers
        self.client.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
    async def create_content_task(self, content_data: Dict) -> Dict:
        """Create a task for new content creation."""
        try:
            task_data = {
                'name': f"Create: {content_data['title']}",
                'projects': [self.project_gid],
                'workspace': self.workspace_gid,
                'notes': self._format_content_notes(content_data),
                'due_on': (datetime.now() + content_data.get('deadline', {'days': 3})).strftime('%Y-%m-%d'),
                'tags': self._get_content_tags(content_data)
            }
            
            result = self.client.tasks.create_task(task_data)
            logger.info(f"Created Asana task: {result['gid']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create Asana content task: {e}")
            raise
            
    async def create_lead_task(self, lead_data: Dict) -> Dict:
        """Create a task for lead follow-up."""
        try:
            task_data = {
                'name': f"Lead: {lead_data.get('company_name', 'Unknown')} - {lead_data.get('source')}",
                'projects': [self.project_gid],
                'workspace': self.workspace_gid,
                'notes': self._format_lead_notes(lead_data),
                'due_on': datetime.now().strftime('%Y-%m-%d'),
                'tags': self._get_lead_tags(lead_data)
            }
            
            result = self.client.tasks.create_task(task_data)
            logger.info(f"Created lead task: {result['gid']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create Asana lead task: {e}")
            raise
            
    async def update_task_status(self, task_gid: str, status: str, notes: Optional[str] = None):
        """Update the status of an existing task."""
        try:
            update_data = {
                'completed': status.lower() == 'completed'
            }
            
            if notes:
                update_data['notes'] = notes
                
            result = self.client.tasks.update_task(task_gid, update_data)
            logger.info(f"Updated task {task_gid} status to {status}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            raise
            
    def _format_content_notes(self, content_data: Dict) -> str:
        """Format content data into structured notes."""
        return f"""
# Content Details
- Type: {content_data.get('type', 'Unknown')}
- Platform: {content_data.get('platform', 'Unknown')}
- Target Audience: {', '.join(content_data.get('target_audience', []))}

# Content Brief
{content_data.get('brief', '')}

# Key Points
{self._format_bullet_points(content_data.get('key_points', []))}

# References
{self._format_bullet_points(content_data.get('references', []))}

# Performance Targets
{self._format_bullet_points(content_data.get('targets', []))}
"""

    def _format_lead_notes(self, lead_data: Dict) -> str:
        """Format lead data into structured notes."""
        return f"""
# Lead Information
- Company: {lead_data.get('company_name', 'Unknown')}
- Industry: {lead_data.get('industry', 'Unknown')}
- Source: {lead_data.get('source', 'Unknown')}
- Score: {lead_data.get('qualification_score', 0):.2f}

# Contact Details
{self._format_contact_details(lead_data.get('contact', {}))}

# Engagement History
{self._format_bullet_points(lead_data.get('engagement_history', []))}

# Next Steps
{self._format_bullet_points(lead_data.get('next_steps', []))}
"""

    def _format_bullet_points(self, items: List) -> str:
        """Format a list of items as bullet points."""
        return '\n'.join(f'- {item}' for item in items)
        
    def _format_contact_details(self, contact: Dict) -> str:
        """Format contact details."""
        return '\n'.join([
            f"- Name: {contact.get('name', 'Unknown')}",
            f"- Title: {contact.get('title', 'Unknown')}",
            f"- Email: {contact.get('email', 'Unknown')}",
            f"- Phone: {contact.get('phone', 'Unknown')}"
        ])
        
    def _get_content_tags(self, content_data: Dict) -> List[str]:
        """Get relevant tags for content task."""
        tags = ['content']
        tags.append(content_data.get('platform', '').lower())
        tags.append(content_data.get('type', '').lower())
        return [tag for tag in tags if tag]
        
    def _get_lead_tags(self, lead_data: Dict) -> List[str]:
        """Get relevant tags for lead task."""
        tags = ['lead']
        if lead_data.get('qualification_score', 0) >= 0.7:
            tags.append('qualified')
        tags.append(lead_data.get('industry', '').lower())
        tags.append(lead_data.get('source', '').lower())
        return [tag for tag in tags if tag]
