from asana import Client
from datetime import datetime
from typing import Dict, Optional, List
import os
import json
from pathlib import Path

class AsanaTracker:
    def __init__(self, workspace_gid: str):
        self.client = Client.access_token(os.getenv('ASANA_ACCESS_TOKEN'))
        self.workspace_gid = workspace_gid
        self.project_gid = os.getenv('ASANA_PROJECT_GID')
        
    def create_lead_task(self, lead_data: Dict) -> str:
        """Create a new task for lead tracking"""
        task_data = {
            'name': f"Lead: {lead_data['name']} ({lead_data['email']})",
            'projects': [self.project_gid],
            'workspace': self.workspace_gid,
            'notes': self._format_lead_notes(lead_data),
            'custom_fields': {
                'lead_score': lead_data.get('score', 0),
                'lead_status': 'new',
                'lead_source': lead_data.get('source', 'website')
            }
        }
        
        result = self.client.tasks.create(task_data)
        return result['gid']
        
    def track_communication(self, task_gid: str, channel: str, 
                          content: str, direction: str = 'outbound',
                          response: Optional[str] = None):
        """Track a communication event"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Get existing task
        task = self.client.tasks.find_by_id(task_gid)
        
        # Format new communication entry
        entry = f"\n🔔 {timestamp} | {channel.upper()} | {direction}\n"
        entry += f"{'➡️' if direction == 'outbound' else '⬅️'} {content}\n"
        
        if response:
            entry += f"↩️ Response: {response}\n"
            
        # Add social links if available
        if channel in ['linkedin', 'facebook', 'instagram']:
            entry += f"🔗 Link: {content.get('url', 'N/A')}\n"
            
        # Update task notes
        updated_notes = task['notes'] + entry
        
        # Update task
        self.client.tasks.update(task_gid, {
            'notes': updated_notes,
            'custom_fields': {
                'last_contact': timestamp,
                'last_channel': channel
            }
        })
        
    def update_lead_score(self, task_gid: str, new_score: float):
        """Update lead score in Asana"""
        self.client.tasks.update(task_gid, {
            'custom_fields': {
                'lead_score': new_score
            }
        })
        
    def track_social_engagement(self, task_gid: str, platform: str, 
                              action: str, details: Dict):
        """Track social media engagement"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"\n📱 {timestamp} | {platform.upper()} Engagement\n"
        entry += f"Action: {action}\n"
        
        if 'url' in details:
            entry += f"URL: {details['url']}\n"
        if 'content' in details:
            entry += f"Content: {details['content']}\n"
        if 'metrics' in details:
            entry += f"Metrics: {json.dumps(details['metrics'], indent=2)}\n"
            
        # Update task notes
        task = self.client.tasks.find_by_id(task_gid)
        updated_notes = task['notes'] + entry
        
        self.client.tasks.update(task_gid, {
            'notes': updated_notes,
            'custom_fields': {
                'last_engagement': timestamp,
                'engagement_platform': platform
            }
        })
        
    def _format_lead_notes(self, lead_data: Dict) -> str:
        """Format lead data for task notes"""
        notes = f"# Lead Information\n\n"
        notes += f"Name: {lead_data['name']}\n"
        notes += f"Email: {lead_data['email']}\n"
        notes += f"Phone: {lead_data.get('phone', 'N/A')}\n"
        notes += f"Source: {lead_data.get('source', 'N/A')}\n"
        notes += f"Initial Score: {lead_data.get('score', 0)}\n\n"
        
        if 'company' in lead_data:
            notes += f"## Company Information\n"
            notes += f"Company: {lead_data['company'].get('name', 'N/A')}\n"
            notes += f"Industry: {lead_data['company'].get('industry', 'N/A')}\n"
            notes += f"Size: {lead_data['company'].get('size', 'N/A')}\n\n"
            
        notes += f"## Social Profiles\n"
        for platform in ['linkedin', 'facebook', 'instagram']:
            if platform in lead_data.get('social_profiles', {}):
                notes += f"{platform.title()}: {lead_data['social_profiles'][platform]}\n"
                
        notes += f"\n## Communication History\n"
        return notes
        
    def create_ab_test(self, name: str, variants: List[str], 
                      success_metric: str) -> str:
        """Create an A/B test tracking project"""
        project_data = {
            'name': f"A/B Test: {name}",
            'workspace': self.workspace_gid,
            'custom_fields': {
                'test_status': 'running',
                'variants': json.dumps(variants),
                'success_metric': success_metric
            }
        }
        
        result = self.client.projects.create(project_data)
        return result['gid']
        
    def track_ab_test_result(self, test_gid: str, variant: str, 
                            lead_gid: str, success: bool):
        """Track A/B test result"""
        task_data = {
            'name': f"Test Result: {variant}",
            'projects': [test_gid],
            'workspace': self.workspace_gid,
            'custom_fields': {
                'variant': variant,
                'success': success,
                'lead_task': lead_gid
            }
        }
        
        self.client.tasks.create(task_data)
