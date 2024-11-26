import asana
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

class AsanaIntegration:
    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.getenv('ASANA_ACCESS_TOKEN')
        if not self.access_token:
            raise ValueError("Asana access token is required")
        
        self.client = asana.Client.access_token(self.access_token)
        self.setup_logging()
        self.workspace_gid = None
        self.project_gid = None
        self.section_gids = {}
        
        # Initialize workspace and project
        self.setup_workspace()

    def setup_logging(self):
        """Set up logging for Asana integration"""
        logging.basicConfig(
            filename='asana_integration.log',
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('AsanaIntegration')

    def setup_workspace(self):
        """Setup or get the AI Agent workspace and project"""
        try:
            # Get or create workspace
            workspaces = list(self.client.workspaces.find_all())
            workspace = next(
                (w for w in workspaces if w['name'] == 'AI Agent Tasks'),
                None
            )
            
            if not workspace:
                self.logger.info("Creating new workspace: AI Agent Tasks")
                workspace = self.client.workspaces.create({'name': 'AI Agent Tasks'})
            
            self.workspace_gid = workspace['gid']
            
            # Get or create project
            projects = list(self.client.projects.find_all({'workspace': self.workspace_gid}))
            project = next(
                (p for p in projects if p['name'] == 'Perpetual Tasks'),
                None
            )
            
            if not project:
                self.logger.info("Creating new project: Perpetual Tasks")
                project = self.client.projects.create_in_workspace(
                    self.workspace_gid,
                    {'name': 'Perpetual Tasks'}
                )
            
            self.project_gid = project['gid']
            
            # Create sections if they don't exist
            self.create_sections()
            
        except Exception as e:
            self.logger.error(f"Error setting up workspace: {str(e)}")
            raise

    def create_sections(self):
        """Create sections for different task types"""
        sections = [
            "Social Media Management",
            "Website Monitoring",
            "Email Management",
            "System Control",
            "Web Automation",
            "System Maintenance"
        ]
        
        try:
            existing_sections = list(self.client.sections.find_by_project(self.project_gid))
            
            for section_name in sections:
                section = next(
                    (s for s in existing_sections if s['name'] == section_name),
                    None
                )
                
                if not section:
                    self.logger.info(f"Creating new section: {section_name}")
                    section = self.client.sections.create_in_project(
                        self.project_gid,
                        {'name': section_name}
                    )
                
                self.section_gids[section_name] = section['gid']
                
        except Exception as e:
            self.logger.error(f"Error creating sections: {str(e)}")

    def get_section_for_task(self, task_type: str) -> str:
        """Map task type to Asana section"""
        section_mapping = {
            'instagram': 'Social Media Management',
            'website_monitor': 'Website Monitoring',
            'email_management': 'Email Management',
            'system_maintenance': 'System Maintenance',
            'web_automation': 'Web Automation'
        }
        return section_mapping.get(task_type, 'System Control')

    def create_task(self, task_id: str, task_type: str, parameters: Dict, status: str = "Active") -> Optional[str]:
        """Create a task in Asana"""
        try:
            section_name = self.get_section_for_task(task_type)
            section_gid = self.section_gids.get(section_name)
            
            if not section_gid:
                self.logger.error(f"Section not found for task type: {task_type}")
                return None
            
            # Create task description
            description = f"""
Task ID: {task_id}
Type: {task_type}
Status: {status}
Parameters:
{self._format_parameters(parameters)}
            """
            
            # Create the task
            task = self.client.tasks.create_in_workspace(
                self.workspace_gid,
                {
                    'name': f"{task_type.replace('_', ' ').title()} - {task_id}",
                    'projects': [self.project_gid],
                    'memberships': [{'project': self.project_gid, 'section': section_gid}],
                    'notes': description,
                    'due_on': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
                    'tags': ['ai-agent', task_type, status.lower()]
                }
            )
            
            self.logger.info(f"Created Asana task: {task['gid']}")
            return task['gid']
            
        except Exception as e:
            self.logger.error(f"Error creating task: {str(e)}")
            return None

    def update_task_status(self, asana_task_gid: str, status: str, error: str = None):
        """Update task status in Asana"""
        try:
            # Get current task data
            task = self.client.tasks.find_by_id(asana_task_gid)
            notes = task['notes']
            
            # Update status in notes
            status_line = f"Status: {status}"
            if error:
                status_line += f"\nError: {error}"
            
            updated_notes = notes.replace(
                f"Status: {task.get('status', 'Active')}",
                status_line
            )
            
            # Update the task
            self.client.tasks.update(
                asana_task_gid,
                {
                    'notes': updated_notes,
                    'tags': ['ai-agent', task['tags'][1], status.lower()]
                }
            )
            
            self.logger.info(f"Updated task status: {asana_task_gid} -> {status}")
            
        except Exception as e:
            self.logger.error(f"Error updating task status: {str(e)}")

    def delete_task(self, asana_task_gid: str):
        """Delete a task from Asana"""
        try:
            self.client.tasks.delete(asana_task_gid)
            self.logger.info(f"Deleted task: {asana_task_gid}")
        except Exception as e:
            self.logger.error(f"Error deleting task: {str(e)}")

    def _format_parameters(self, parameters: Dict) -> str:
        """Format task parameters for display"""
        formatted = []
        for key, value in parameters.items():
            if key in ['password', 'api_key', 'token']:
                value = '********'
            formatted.append(f"- {key}: {value}")
        return "\n".join(formatted)

    def get_task_status(self, asana_task_gid: str) -> Optional[str]:
        """Get task status from Asana"""
        try:
            task = self.client.tasks.find_by_id(asana_task_gid)
            notes = task['notes']
            
            # Extract status from notes
            for line in notes.split('\n'):
                if line.startswith('Status:'):
                    return line.replace('Status:', '').strip()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting task status: {str(e)}")
            return None
