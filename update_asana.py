from agents.sync_tasks import TaskSyncManager
from agents.asana_manager import AsanaManager
import asyncio
import json
from datetime import datetime

async def update_all_asana_tasks():
    """Update all tasks in Asana with latest information."""
    try:
        # Initialize managers
        sync_manager = TaskSyncManager()
        asana_manager = AsanaManager()
        
        print("Starting Asana task update...")
        
        # Load current task state
        state = sync_manager.load_task_state()
        
        # Get all tasks from Asana
        asana_tasks = asana_manager.get_tasks_by_status("all")
        
        # Update each task
        for task in asana_tasks:
            task_id = task.get('gid')
            task_name = task.get('name', 'Unknown Task')
            
            print(f"\nUpdating task: {task_name}")
            
            # Get agent data from task description
            agent_data = {
                'name': task_name.replace('Agent: ', '') if task_name.startswith('Agent: ') else task_name,
                'email': task.get('agent_email', ''),
                'status': task.get('status', 'New Lead'),
                'description': task.get('notes', ''),
                'communications': []
            }
            
            # Add any recent communications
            if 'stories' in task:
                for story in task['stories']:
                    if story.get('type') == 'comment':
                        agent_data['communications'].append({
                            'date': story.get('created_at'),
                            'platform': 'Asana',
                            'status': 'Logged',
                            'details': story.get('text', '')
                        })
            
            # Update task in our system
            success = sync_manager.update_agent_communication(agent_data)
            if success:
                print(f"Successfully updated {task_name}")
            else:
                print(f"Failed to update {task_name}")
        
        print("\nTask update complete!")
        
    except Exception as e:
        print(f"Error updating tasks: {str(e)}")

if __name__ == "__main__":
    asyncio.run(update_all_asana_tasks())
