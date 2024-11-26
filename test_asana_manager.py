import asyncio
import logging
from agents.asana_manager import AsanaManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('asana_manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('AsanaTest')

async def test_asana_manager():
    """Test Asana manager functionality"""
    try:
        # Initialize agent
        agent = AsanaManager()
        
        # Test project creation
        logger.info("Testing project creation...")
        project_data = {
            'name': 'Q4 Marketing Campaign',
            'description': 'Q4 2023 Marketing Initiatives',
            'team': 'Marketing',
            'due_date': '2023-12-31'
        }
        project = await agent.create_project(project_data)
        logger.info(f"Created project: {project['name']}")
        
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
            logger.info(f"Created task: {task['name']}")
        
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
        
        # Test reporting
        logger.info("\nTesting reporting...")
        report = await agent.generate_project_report(project['id'])
        logger.info("Project Report:")
        logger.info(f"- Status: {report['status']}")
        logger.info(f"- Blockers: {len(report['blockers'])}")
        logger.info(f"- Next actions: {len(report['next_actions'])}")
        
        # Cleanup
        logger.info("\nCleaning up...")
        await agent.cleanup()
        
    except Exception as e:
        logger.error(f"Error in Asana manager test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_asana_manager())
