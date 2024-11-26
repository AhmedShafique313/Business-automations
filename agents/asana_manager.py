import json
import logging
from datetime import datetime
import pandas as pd
import asana
from playwright.async_api import async_playwright
import asyncio
from typing import Dict, Optional, List
import os
import re
from .research_manager import ResearchManager

class AsanaManager:
    def __init__(self):
        """Initialize the Asana manager."""
        self.setup_logging()
        self.client = None
        self.workspace_gid = None
        self.project_gid = None
        self.sections = {}
        self.research_manager = ResearchManager()

    def setup_logging(self):
        """Set up logging for the Asana manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('asana_manager.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('AsanaManager')

    def setup_client(self):
        """Set up the Asana client."""
        try:
            # Get API key from environment
            api_key = os.getenv('ASANA_ACCESS_TOKEN')
            if not api_key:
                raise ValueError("ASANA_ACCESS_TOKEN environment variable not set")

            # Initialize client
            self.client = asana.Client.access_token(api_key)
            self.client.headers = {'asana-enable': 'string_ids,new_sections'}

            # Get workspace
            workspaces = list(self.client.workspaces.get_workspaces())
            if not workspaces:
                raise ValueError("No workspaces found")
            self.workspace_gid = workspaces[0]['gid']

            # Set up project structure
            self.setup_project_structure()

            self.logger.info("Asana client setup complete")

        except Exception as e:
            self.logger.error(f"Error setting up Asana client: {str(e)}")
            raise

    async def _init_browser(self):
        """Initialize browser with optimized settings."""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                ]
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True
            )
            self.page = await self.context.new_page()
            await self.page.set_default_timeout(60000)  # 60 second timeout

    async def _close_browser(self):
        """Close browser and cleanup resources."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    def update_agent_research(self, task_gid: str, research_data: Dict) -> bool:
        """Update task with new research findings."""
        try:
            if not self.client:
                self.setup_client()

            # Process research data
            research = self.research_manager.process_research(task_gid, research_data)
            
            # Format the research data into a structured description
            description = self._format_research_description(research)
            
            # Get the task first
            task = self.client.tasks.get_task(task_gid)
            if not task:
                self.logger.error(f"Task {task_gid} not found")
                return False
            
            # Update task description using the Asana API
            updated_task = self.client.tasks.update_task(
                task_gid,
                {'notes': description}
            )
            
            if not updated_task:
                self.logger.error("Failed to update task")
                return False
            
            self.logger.info(f"Successfully updated task {task_gid} with research data")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating task with research: {str(e)}")
            return False

    def _format_research_description(self, research_data: Dict) -> str:
        """Format research data into a structured description."""
        try:
            social_profiles = research_data.get('social_profiles', {})
            
            def format_social_profile(platform: str) -> str:
                url = social_profiles.get(platform.lower())
                if url and url.lower() != 'not found':
                    return f"✅ {platform}: {url}"
                return f"❌ {platform}: Not found"

            def format_bullet_points(items: List[str]) -> str:
                if not items or (len(items) == 1 and items[0].startswith('No specific')):
                    return "• None identified yet"
                return "\n".join(f"• {item}" for item in items)

            def format_listings(listings: List[str]) -> str:
                if not listings:
                    return "• No current listings found"
                return "\n".join(f"• {listing}" for listing in listings)

            description = f"""📊 AGENT RESEARCH REPORT
======================

📋 BASIC INFORMATION
------------------
Name: {research_data.get('name', 'Unknown')}
Brokerage: {research_data.get('brokerage', 'Unknown')}
Office: {research_data.get('office', 'Unknown')}
Location: {research_data.get('location', 'Unknown')}

📞 CONTACT INFORMATION
-------------------
Email: {research_data.get('contact_info', {}).get('email', 'Not found')}
Phone: {research_data.get('contact_info', {}).get('phone', 'Not found')}
Office Phone: {research_data.get('contact_info', {}).get('office_phone', 'Not found')}

🌐 SOCIAL MEDIA PROFILES
---------------------
{format_social_profile('LinkedIn')}
{format_social_profile('Instagram')}
{format_social_profile('Facebook')}
{format_social_profile('Twitter')}
{format_social_profile('Zillow')}
{format_social_profile('Realtor')}
{format_social_profile('Youtube')}

🏠 CURRENT LISTINGS
----------------
{format_listings(research_data.get('listings', []))}

👤 PERSONALITY ANALYSIS
--------------------
Communication Style: {research_data.get('personality', {}).get('communication_style', 'Unknown')}
Content Focus: {research_data.get('personality', {}).get('content_focus', 'Unknown')}
Social Media Engagement: {research_data.get('personality', {}).get('social_engagement', 'Unknown')}

💡 CAMPAIGN INSIGHTS
-----------------
VALUE PROPOSITIONS:
{format_bullet_points(research_data.get('value_props', ['No specific value propositions identified']))}

PERSONALIZATION POINTS:
{format_bullet_points(research_data.get('personalization_points', ['No specific personalization points identified']))}

SUGGESTED APPROACH:
{research_data.get('suggested_approach', 'No specific approach suggested yet')}

📈 RESEARCH QUALITY
----------------
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Quality Score: {research_data.get('data_quality_score', 'N/A')}/10"""

            return description
            
        except Exception as e:
            self.logger.error(f"Error formatting research description: {str(e)}")
            return "Error formatting research data"

    def add_agent_task(self, agent_data: Dict) -> Optional[str]:
        """Add a new agent task to Asana."""
        try:
            if not self.client:
                self.setup_client()

            # Format initial research description
            initial_research = {
                'name': agent_data.get('name', ''),
                'brokerage': agent_data.get('brokerage', ''),
                'office': agent_data.get('office', ''),
                'location': agent_data.get('location', ''),
                'contact_info': {},
                'social_profiles': {},
                'listings': [],
                'personality': {},
                'value_props': [],
                'personalization_points': [],
                'suggested_approach': None,
                'data_quality_score': 0
            }
            
            # Format the description
            description = self._format_research_description(initial_research)
            
            # Create task with initial description
            task = self.client.tasks.create_in_workspace(
                workspace=self.workspace_gid,
                data={
                    'name': agent_data.get('name', 'Unknown Agent'),
                    'notes': description,
                    'projects': [self.project_gid]
                }
            )
            
            task_gid = task.get('gid')
            if not task_gid:
                self.logger.error("Failed to get task GID")
                return None
            
            # Add to Research section
            section_gid = self.sections.get('Research')
            if section_gid:
                self.client.sections.add_task(section_gid, {'task': task_gid})
            
            self.logger.info(f"Successfully created task for agent {agent_data.get('name')}")
            return task_gid
            
        except Exception as e:
            self.logger.error(f"Error adding agent task: {str(e)}")
            return None

    def setup_project_structure(self):
        """Set up the project structure with sections."""
        try:
            # Create main project if it doesn't exist
            project_name = "Agent Research"
            
            # Get all projects in workspace
            projects = list(self.client.projects.find_all({'workspace': self.workspace_gid}))
            
            project_exists = False
            for project in projects:
                if project['name'] == project_name:
                    self.project_gid = project['gid']
                    project_exists = True
                    break
            
            if not project_exists:
                result = self.client.projects.create_project({
                    'name': project_name,
                    'workspace': self.workspace_gid,
                    'notes': 'Automated task management for real estate agent research',
                    'default_view': 'list',
                    'privacy_setting': 'private'
                })
                self.project_gid = result['gid']
            
            # Create sections if they don't exist
            self.sections = {
                'New Leads': self._get_or_create_section('New Leads'),
                'In Progress': self._get_or_create_section('In Progress'),
                'Completed': self._get_or_create_section('Completed'),
                'Not Interested': self._get_or_create_section('Not Interested'),
                'Research': self._get_or_create_section('Research')
            }
            
            self.logger.info("Project structure setup complete")
            
        except Exception as e:
            self.logger.error(f"Error setting up project structure: {str(e)}")
            raise

    def _get_or_create_section(self, section_name: str) -> str:
        """Get or create a section in the project."""
        try:
            # Get all sections in the project
            sections = list(self.client.sections.get_sections_for_project(self.project_gid))
            
            # Check if section exists
            for section in sections:
                if section['name'] == section_name:
                    return section['gid']
            
            # Create new section if it doesn't exist
            result = self.client.sections.create_section_for_project(
                self.project_gid,
                {'name': section_name}
            )
            return result['gid']
            
        except Exception as e:
            self.logger.error(f"Error getting/creating section {section_name}: {str(e)}")
            raise

    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks from the project."""
        try:
            # Get project tasks
            tasks = self.client.tasks.get_tasks_for_project(
                self.project_gid,
                {
                    'opt_fields': ['name', 'notes', 'completed', 'assignee', 'due_on', 'tags'],
                    'completed_since': 'now'  # Only get incomplete tasks
                }
            )
            
            # Filter for agent tasks
            agent_tasks = [
                task for task in tasks
                if task.get('name', '').startswith('Agent: ') and not task.get('completed')
            ]
            
            self.logger.info(f"Found {len(agent_tasks)} active agent tasks")
            return agent_tasks
            
        except Exception as e:
            self.logger.error(f"Error getting tasks: {str(e)}")
            return []

    async def update_task_status(self, task_gid: str, status: str) -> bool:
        """Update the status of a task with improved error handling."""
        try:
            await self._init_browser()
            
            # Navigate to task page
            await self.page.goto(f"https://app.asana.com/0/{self.project_gid}/{task_gid}")
            
            # Wait for status dropdown
            status_selector = '[aria-label="Status"]'
            await self._wait_for_selector(status_selector)
            
            # Click status dropdown
            await self.page.click(status_selector)
            
            # Wait for and click status option
            status_option = f'[role="option"][data-value="{status}"]'
            await self._wait_for_selector(status_option)
            await self.page.click(status_option)
            
            # Wait for update to complete
            await self.page.wait_for_load_state("networkidle")
            
            self.logger.info(f"Updated task {task_gid} status to {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating task status: {str(e)}")
            return False
        finally:
            await self._close_browser()

    async def _wait_for_selector(self, selector: str, timeout: int = 60000):
        """Wait for a selector with custom timeout."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
        except Exception as e:
            self.logger.error(f"Timeout waiting for selector {selector}: {str(e)}")
            raise

    def add_communication(self, task_gid: str, comm_type: str, details: str) -> bool:
        """Add a communication record to the task."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Format the communication based on type
            if comm_type == 'email':
                comment = f"""📧 Email Communication - {timestamp}
Subject: {details.get('subject', 'N/A')}
Status: {details.get('status', 'Sent')}
---
{details.get('body', '')}"""

            elif comm_type == 'social':
                comment = f"""💬 Social Media Interaction - {timestamp}
Platform: {details.get('platform', 'N/A')}
Type: {details.get('type', 'N/A')}
---
{details.get('content', '')}"""

            elif comm_type == 'campaign':
                comment = f"""📢 Campaign Activity - {timestamp}
Campaign: {details.get('campaign_name', 'N/A')}
Action: {details.get('action', 'N/A')}
Status: {details.get('status', 'N/A')}
---
{details.get('details', '')}"""

            elif comm_type == 'response':
                comment = f"""📥 Agent Response - {timestamp}
Channel: {details.get('channel', 'N/A')}
---
{details.get('message', '')}"""

            elif comm_type == 'system':
                comment = f"""🤖 System Update - {timestamp}
{details}"""

            else:
                comment = f"""📝 Communication Log - {timestamp}
Type: {comm_type}
---
{details}"""

            # Add the comment to the task
            self.client.tasks.add_comment(task_gid, {'text': comment})
            return True

        except Exception as e:
            self.logger.error(f"Error adding communication: {str(e)}")
            return False

    def update_all_tasks(self) -> bool:
        """
        Update all tasks in the Agent Research project with standardized formatting.
        
        Returns:
            bool: True if all tasks were processed successfully, False otherwise
        """
        try:
            # Get all tasks in the project
            tasks = self.client.tasks.find_all(
                project=self.project_gid, 
                opt_fields=['name', 'notes', 'completed']
            )
            
            # Track success of updates
            total_tasks = 0
            successful_updates = 0
            
            # Process each task
            for task in tasks:
                total_tasks += 1
                try:
                    # Skip completed tasks
                    if task.get('completed', False):
                        logging.info(f"Skipping completed task: {task['name']}")
                        continue
                    
                    # Parse existing research data
                    existing_data = self._parse_existing_research(task.get('notes', ''))
                    
                    # Update task description
                    updated_description = self._format_research_description(existing_data)
                    
                    # Update task in Asana
                    self.client.tasks.update(task['gid'], {
                        'notes': updated_description
                    })
                    
                    successful_updates += 1
                    logging.info(f"Successfully updated task: {task['name']}")
                
                except Exception as task_error:
                    logging.error(f"Error updating task {task.get('name', 'Unknown')}: {str(task_error)}")
            
            # Log summary
            logging.info(f"Task Update Summary: {successful_updates}/{total_tasks} tasks updated")
            
            return successful_updates == total_tasks
        
        except Exception as e:
            logging.error(f"Critical error in update_all_tasks: {str(e)}")
            return False

    def _parse_existing_research(self, notes: str) -> Dict:
        """Parse existing research data from task notes."""
        data = {
            'name': '',
            'brokerage': '',
            'office': '',
            'location': '',
            'contact_info': {},
            'social_profiles': {},
            'listings': [],
            'personality': {},
            'value_props': [],
            'personalization_points': [],
            'suggested_approach': None,
            'data_quality_score': 0
        }
        
        try:
            # Extract basic information
            name_match = re.search(r'Name:\s*([^\n]+)', notes)
            if name_match:
                data['name'] = name_match.group(1).strip()

            brokerage_match = re.search(r'Brokerage:\s*([^\n]+)', notes)
            if brokerage_match:
                data['brokerage'] = brokerage_match.group(1).strip()

            office_match = re.search(r'Office:\s*([^\n]+)', notes)
            if office_match:
                data['office'] = office_match.group(1).strip()

            location_match = re.search(r'Location:\s*([^\n]+)', notes)
            if location_match:
                data['location'] = location_match.group(1).strip()

            # Extract contact information
            email_match = re.search(r'Email:\s*([^\n]+)', notes)
            if email_match:
                data['contact_info']['email'] = email_match.group(1).strip()

            phone_match = re.search(r'Phone:\s*([^\n]+)', notes)
            if phone_match:
                data['contact_info']['phone'] = phone_match.group(1).strip()

            office_phone_match = re.search(r'Office Phone:\s*([^\n]+)', notes)
            if office_phone_match:
                data['contact_info']['office_phone'] = office_phone_match.group(1).strip()

            # Extract social profiles
            social_platforms = ['LinkedIn', 'Instagram', 'Facebook', 'Twitter', 'Zillow', 'Realtor', 'Youtube']
            for platform in social_platforms:
                pattern = rf'{platform}:\s*([^\n✅❌]+)'
                match = re.search(pattern, notes)
                if match:
                    url = match.group(1).strip()
                    if url.lower() != 'not found':
                        data['social_profiles'][platform.lower()] = url

            # Extract personality information
            comm_style_match = re.search(r'Communication Style:\s*([^\n]+)', notes)
            if comm_style_match:
                data['personality']['communication_style'] = comm_style_match.group(1).strip()

            content_focus_match = re.search(r'Content Focus:\s*([^\n]+)', notes)
            if content_focus_match:
                data['personality']['content_focus'] = content_focus_match.group(1).strip()

            engagement_match = re.search(r'Social Media Engagement:\s*([^\n]+)', notes)
            if engagement_match:
                data['personality']['social_engagement'] = engagement_match.group(1).strip()

            # Extract listings
            listings_section = re.search(r'Current Listings\n-*\n(.*?)\n\n', notes, re.DOTALL)
            if listings_section:
                listings = listings_section.group(1).strip()
                if listings and 'No current listings found' not in listings:
                    data['listings'] = [line.strip('• ').strip() for line in listings.split('\n') if line.strip()]

            # Extract value propositions
            value_props_section = re.search(r'Value Propositions:\n(.*?)\n\n', notes, re.DOTALL)
            if value_props_section:
                props = value_props_section.group(1).strip()
                if props and 'None identified yet' not in props:
                    data['value_props'] = [line.strip('• ').strip() for line in props.split('\n') if line.strip()]

            # Extract personalization points
            personalization_section = re.search(r'Personalization Points:\n(.*?)\n\n', notes, re.DOTALL)
            if personalization_section:
                points = personalization_section.group(1).strip()
                if points and 'None identified yet' not in points:
                    data['personalization_points'] = [line.strip('• ').strip() for line in points.split('\n') if line.strip()]

            # Extract suggested approach
            approach_section = re.search(r'Suggested Approach:\n(.*?)\n\n', notes, re.DOTALL)
            if approach_section:
                approach = approach_section.group(1).strip()
                if approach and 'No specific approach suggested' not in approach:
                    data['suggested_approach'] = approach

            return data

        except Exception as e:
            self.logger.error(f"Error parsing existing research: {str(e)}")
            return data

if __name__ == "__main__":
    # Initialize Asana manager
    manager = AsanaManager()
    
    # Test creating a task
    test_agent = {
        'name': 'Test Agent',
        'brokerage': 'Test Brokerage',
        'location': 'Test Location',
        'description': 'This is a test agent',
        'is_luxury': True
    }
    manager.add_agent_task(test_agent)
