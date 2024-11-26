import json
import logging
from datetime import datetime
from .asana_manager import AsanaManager
import os

class TaskSyncManager:
    def __init__(self):
        self.setup_logging()
        self.asana_manager = AsanaManager()
        self.task_state_file = 'task_state.json'

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('task_sync.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('TaskSyncManager')

    def load_task_state(self):
        try:
            with open(self.task_state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "tasks": [],
                "lastUpdate": None,
                "asanaSync": {
                    "lastSync": None,
                    "status": "idle"
                }
            }

    def save_task_state(self, state):
        with open(self.task_state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def sync_tasks(self):
        try:
            self.logger.info("Starting task synchronization")
            
            # Update sync status
            state = self.load_task_state()
            state['asanaSync']['status'] = 'syncing'
            self.save_task_state(state)

            # Fetch tasks from Asana
            tasks = self.asana_manager.get_all_tasks()
            
            # Transform tasks to our format
            formatted_tasks = []
            for task in tasks:
                formatted_task = {
                    'id': task['gid'],
                    'name': task['name'],
                    'description': task.get('notes', ''),
                    'status': 'completed' if task.get('completed') else 'in_progress' if task.get('started') else 'todo',
                    'priority': task.get('priority', 'medium'),
                    'dueDate': task.get('due_on'),
                    'assignee': task.get('assignee', {}).get('name'),
                    'asanaId': task['gid']
                }
                formatted_tasks.append(formatted_task)

            # Update state
            state['tasks'] = formatted_tasks
            state['lastUpdate'] = datetime.now().isoformat()
            state['asanaSync'] = {
                'lastSync': datetime.now().isoformat(),
                'status': 'idle'
            }
            
            self.save_task_state(state)
            self.logger.info(f"Successfully synced {len(formatted_tasks)} tasks")
            
        except Exception as e:
            self.logger.error(f"Error syncing tasks: {str(e)}")
            state = self.load_task_state()
            state['asanaSync']['status'] = 'error'
            self.save_task_state(state)
            raise

    def update_agent_communication(self, agent_data):
        """Update Asana task with agent communication details."""
        try:
            self.logger.info(f"Updating task for agent: {agent_data.get('name', 'Unknown')}")
            
            # Load existing state
            state = self.load_task_state()
            
            # Find existing task for this agent
            existing_task = None
            for task in state['tasks']:
                if task.get('agent_email') == agent_data.get('email'):
                    existing_task = task
                    break
            
            # Create or update task in Asana
            task_data = {
                'name': f"Agent: {agent_data.get('name', 'Unknown')}",
                'description': self._format_agent_description(agent_data),
                'status': agent_data.get('status', 'New Lead'),
                'agent_email': agent_data.get('email'),
                'last_updated': datetime.now().isoformat()
            }
            
            if existing_task:
                # Update existing task
                self.asana_manager.update_task(existing_task['asanaId'], task_data)
                task_data['asanaId'] = existing_task['asanaId']
                task_data['id'] = existing_task['id']
            else:
                # Create new task
                asana_task = self.asana_manager.create_task_for_agent(task_data)
                if asana_task:
                    task_data['asanaId'] = asana_task['gid']
                    task_data['id'] = asana_task['gid']
                    state['tasks'].append(task_data)
            
            # Update state
            self.save_task_state(state)
            self.logger.info(f"Successfully updated task for agent {agent_data.get('name')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating agent communication: {str(e)}")
            return False

    def _format_agent_description(self, agent_data):
        """Format agent data into a structured description."""
        description = []
        description.append("# Agent Information")
        description.append(f"Name: {agent_data.get('name', 'Unknown')}")
        description.append(f"Email: {agent_data.get('email', 'N/A')}")
        description.append(f"Phone: {agent_data.get('phone', 'N/A')}")
        description.append(f"Agency: {agent_data.get('agency', 'N/A')}")
        
        # Communication History
        description.append("\n# Communication History")
        if 'communications' in agent_data:
            for comm in agent_data['communications']:
                description.append(f"\n## {comm.get('date', 'Unknown Date')} - {comm.get('platform', 'Unknown Platform')}")
                description.append(f"Status: {comm.get('status', 'Unknown')}")
                description.append(f"Details: {comm.get('details', 'No details provided')}")
        
        # Properties
        if 'properties' in agent_data:
            description.append("\n# Properties")
            for prop in agent_data['properties']:
                description.append(f"\n- {prop.get('address', 'Unknown Address')}")
                description.append(f"  Price: {prop.get('price', 'N/A')}")
                description.append(f"  Status: {prop.get('status', 'N/A')}")
        
        # Notes
        if agent_data.get('notes'):
            description.append("\n# Additional Notes")
            description.append(agent_data['notes'])
        
        return "\n".join(description)

if __name__ == "__main__":
    sync_manager = TaskSyncManager()
    sync_manager.sync_tasks()
