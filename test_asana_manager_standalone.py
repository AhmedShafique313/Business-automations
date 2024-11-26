import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('asana_manager_standalone.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('AsanaTest')

class AsanaManagerStandalone:
    """Standalone version of Asana manager for testing."""
    
    def __init__(self):
        """Initialize the Asana manager"""
        self.projects = {}
        self.tasks = {}
        self.task_dependencies = {}
        self.task_counter = 1000
        self.project_counter = 1000
        
    async def create_project(self, project_data: Dict) -> Dict:
        """Create a new project."""
        project_id = str(self.project_counter)
        self.project_counter += 1
        
        project = {
            'id': project_id,
            'name': project_data['name'],
            'description': project_data.get('description', ''),
            'team': project_data.get('team', ''),
            'due_date': project_data.get('due_date', ''),
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'tasks': []
        }
        
        self.projects[project_id] = project
        return project
        
    async def create_task(self, project_id: str, task_data: Dict) -> Dict:
        """Create a new task in a project."""
        task_id = str(self.task_counter)
        self.task_counter += 1
        
        task = {
            'id': task_id,
            'name': task_data['name'],
            'description': task_data.get('description', ''),
            'assignee': task_data.get('assignee', ''),
            'due_date': task_data.get('due_date', ''),
            'priority': task_data.get('priority', 'medium'),
            'status': 'not_started',
            'project_id': project_id,
            'created_at': datetime.now().isoformat()
        }
        
        self.tasks[task_id] = task
        self.projects[project_id]['tasks'].append(task_id)
        return task
        
    async def assign_task(self, task_id: str, assignee: str) -> Dict:
        """Assign a task to a team member."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
            
        self.tasks[task_id]['assignee'] = assignee
        return {
            'task_id': task_id,
            'assignee': assignee,
            'status': 'assigned'
        }
        
    async def update_task_status(self, task_id: str, status: str) -> str:
        """Update task status."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
            
        valid_statuses = ['not_started', 'in_progress', 'completed', 'on_hold']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
            
        self.tasks[task_id]['status'] = status
        return status
        
    async def set_task_dependency(self, dependent_task_id: str, dependency_task_id: str) -> Dict:
        """Set task dependencies."""
        if dependent_task_id not in self.tasks or dependency_task_id not in self.tasks:
            raise ValueError("One or both tasks not found")
            
        if dependent_task_id not in self.task_dependencies:
            self.task_dependencies[dependent_task_id] = []
            
        self.task_dependencies[dependent_task_id].append(dependency_task_id)
        
        return {
            'dependent_task': dependent_task_id,
            'dependency_task': dependency_task_id,
            'status': 'set'
        }
        
    async def track_project_progress(self, project_id: str) -> Dict:
        """Track project progress."""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
            
        project = self.projects[project_id]
        total_tasks = len(project['tasks'])
        completed_tasks = sum(
            1 for task_id in project['tasks']
            if self.tasks[task_id]['status'] == 'completed'
        )
        
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'completion_percentage': round(completion_percentage, 2),
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'on_track': completion_percentage >= 50  # Simple threshold for demo
        }
        
    async def generate_project_report(self, project_id: str) -> Dict:
        """Generate project status report."""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
            
        project = self.projects[project_id]
        project_tasks = [self.tasks[task_id] for task_id in project['tasks']]
        
        # Find blockers (tasks with dependencies that aren't completed)
        blockers = []
        for task in project_tasks:
            if task['id'] in self.task_dependencies:
                for dep_id in self.task_dependencies[task['id']]:
                    if self.tasks[dep_id]['status'] != 'completed':
                        blockers.append({
                            'task': task['name'],
                            'blocked_by': self.tasks[dep_id]['name']
                        })
        
        # Determine next actions (tasks that are ready to start)
        next_actions = []
        for task in project_tasks:
            if task['status'] == 'not_started':
                if task['id'] not in self.task_dependencies or all(
                    self.tasks[dep_id]['status'] == 'completed'
                    for dep_id in self.task_dependencies[task['id']]
                ):
                    next_actions.append({
                        'task': task['name'],
                        'assignee': task['assignee']
                    })
        
        # Calculate overall status
        completion = await self.track_project_progress(project_id)
        if completion['completion_percentage'] >= 80:
            status = 'on_track'
        elif completion['completion_percentage'] >= 50:
            status = 'at_risk'
        else:
            status = 'behind'
            
        return {
            'status': status,
            'completion': completion,
            'blockers': blockers,
            'next_actions': next_actions
        }
        
    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up resources...")
        self.projects.clear()
        self.tasks.clear()
        self.task_dependencies.clear()

async def test_asana_manager():
    """Test Asana manager functionality"""
    try:
        # Initialize agent
        agent = AsanaManagerStandalone()
        
        # Test project creation
        logger.info("Testing project creation...")
        project_data = {
            'name': 'Q4 Marketing Campaign',
            'description': 'Q4 2023 Marketing Initiatives',
            'team': 'Marketing',
            'due_date': '2023-12-31'
        }
        project = await agent.create_project(project_data)
        logger.info(f"Created project: {project['name']} (ID: {project['id']})")
        
        # Test task creation
        logger.info("\nTesting task creation...")
        tasks = [
            {
                'name': 'Content Creation',
                'description': 'Create content for Q4 campaign',
                'assignee': 'content_team',
                'due_date': '2023-11-30',
                'priority': 'high'
            },
            {
                'name': 'Social Media Schedule',
                'description': 'Plan social media posts for Q4',
                'assignee': 'social_media_team',
                'due_date': '2023-11-15',
                'priority': 'medium'
            }
        ]
        
        created_tasks = []
        for task_data in tasks:
            task = await agent.create_task(project['id'], task_data)
            created_tasks.append(task)
            logger.info(f"Created task: {task['name']} (ID: {task['id']})")
        
        # Test task assignment
        logger.info("\nTesting task assignment...")
        for task in created_tasks:
            assignment = await agent.assign_task(task['id'], task['assignee'])
            logger.info(f"Assigned task '{task['name']}' to {assignment['assignee']}")
        
        # Test task status update
        logger.info("\nTesting task status update...")
        for task in created_tasks:
            status = await agent.update_task_status(task['id'], 'in_progress')
            logger.info(f"Updated task '{task['name']}' status to: {status}")
        
        # Test task dependencies
        logger.info("\nTesting task dependencies...")
        if len(created_tasks) >= 2:
            dependency = await agent.set_task_dependency(
                created_tasks[1]['id'],  # Social Media depends on
                created_tasks[0]['id']   # Content Creation
            )
            logger.info(f"Set dependency: {created_tasks[1]['name']} depends on {created_tasks[0]['name']}")
        
        # Test progress tracking
        logger.info("\nTesting progress tracking...")
        progress = await agent.track_project_progress(project['id'])
        logger.info(f"Project progress:")
        logger.info(f"- Completion: {progress['completion_percentage']}%")
        logger.info(f"- Tasks completed: {progress['completed_tasks']}/{progress['total_tasks']}")
        logger.info(f"- On track: {'Yes' if progress['on_track'] else 'No'}")
        
        # Complete one task
        await agent.update_task_status(created_tasks[0]['id'], 'completed')
        
        # Test reporting
        logger.info("\nTesting reporting...")
        report = await agent.generate_project_report(project['id'])
        logger.info("Project Report:")
        logger.info(f"- Status: {report['status']}")
        logger.info(f"- Blockers: {len(report['blockers'])} found")
        for blocker in report['blockers']:
            logger.info(f"  * {blocker['task']} is blocked by {blocker['blocked_by']}")
        logger.info(f"- Next actions: {len(report['next_actions'])} identified")
        for action in report['next_actions']:
            logger.info(f"  * {action['task']} (Assignee: {action['assignee']})")
        
        # Cleanup
        logger.info("\nCleaning up...")
        await agent.cleanup()
        
    except Exception as e:
        logger.error(f"Error in Asana manager test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_asana_manager())
