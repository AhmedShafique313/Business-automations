"""Task executor for managing and automating business tasks."""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asana
from pythonjsonlogger import jsonlogger

class TaskExecutor:
    """Executes and manages automated business tasks."""
    
    def __init__(self):
        """Initialize task executor with optional Asana integration."""
        self.setup_logging()
        self.asana_client = None
        try:
            self.init_asana_client()
        except Exception as e:
            self.logger.warning(f"Asana integration not available: {str(e)}")
    
    def setup_logging(self):
        """Configure logging for task executor."""
        self.logger = logging.getLogger('TaskExecutor')
        
        # Add JSON formatter if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = jsonlogger.JsonFormatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s',
                timestamp=True
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def init_asana_client(self):
        """Initialize Asana client if credentials are available."""
        access_token = os.getenv('ASANA_ACCESS_TOKEN')
        if access_token:
            try:
                self.asana_client = asana.Client.access_token(access_token)
                self.logger.info("Asana client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Asana client: {str(e)}")
                raise RuntimeError("Asana initialization failed")
        else:
            self.logger.warning("Asana access token not found, continuing without Asana integration")
    
    def schedule_daily_updates(self):
        """Schedule and manage daily task updates."""
        while True:
            try:
                current_time = datetime.now()
                
                # Example scheduled tasks
                if current_time.hour == 9:  # 9 AM
                    self.execute_morning_tasks()
                elif current_time.hour == 14:  # 2 PM
                    self.execute_afternoon_tasks()
                elif current_time.hour == 17:  # 5 PM
                    self.execute_evening_tasks()
                
                # Sleep for an hour before next check
                time.sleep(3600)
            except Exception as e:
                self.logger.error(f"Error in daily updates: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retry
    
    def execute_morning_tasks(self):
        """Execute morning scheduled tasks."""
        self.logger.info("Executing morning tasks")
        # Add your morning task logic here
        pass
    
    def execute_afternoon_tasks(self):
        """Execute afternoon scheduled tasks."""
        self.logger.info("Executing afternoon tasks")
        # Add your afternoon task logic here
        pass
    
    def execute_evening_tasks(self):
        """Execute evening scheduled tasks."""
        self.logger.info("Executing evening tasks")
        # Add your evening task logic here
        pass
    
    def create_task(self, title: str, description: str, due_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Create a new task, in Asana if available, otherwise locally."""
        try:
            if self.asana_client:
                workspace_gid = os.getenv('ASANA_WORKSPACE_GID')
                if workspace_gid:
                    task = self.asana_client.tasks.create_in_workspace(
                        workspace_gid,
                        {'name': title, 'notes': description, 'due_on': due_date}
                    )
                    self.logger.info(f"Created Asana task: {title}")
                    return task
                else:
                    self.logger.warning("Asana workspace GID not found")
            
            # Fallback to local task tracking
            task = {
                'name': title,
                'notes': description,
                'due_on': due_date,
                'created_at': datetime.now(),
                'status': 'pending'
            }
            self.logger.info(f"Created local task: {title}")
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to create task: {str(e)}")
            raise

if __name__ == "__main__":
    executor = TaskExecutor()
    executor.schedule_daily_updates()
