"""Manages scheduled tasks for automated email processing."""
import asyncio
import logging
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import signal
import sys
from typing import Dict, List, Optional

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from agents.email_manager import EmailManager
from agents.email_campaign_analytics import EmailAnalytics
from agents.email_sequence_manager import EmailSequenceManager
from agents.email_sequence_manager import SequenceStep

logger = logging.getLogger(__name__)

class ScheduledTaskManager:
    """Manages scheduled tasks for automated email processing."""
    
    def __init__(self, check_interval: int = 300):
        """Initialize the task manager.
        
        Args:
            check_interval: Time between checks in seconds (default: 5 minutes)
        """
        self.check_interval = check_interval
        self.setup_logging()
        self.running = False
        self.initialize_managers()
        
    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scheduled_tasks.log'),
                logging.StreamHandler()
            ]
        )
    
    def initialize_managers(self):
        """Initialize email and sequence managers."""
        credentials_path = os.path.join(project_root, 'credentials.json')
        self.email_manager = EmailManager(credentials_path)
        self.analytics = EmailAnalytics()
        self.sequence_manager = EmailSequenceManager(
            self.email_manager,
            self.analytics
        )
    
    async def process_database_additions(self):
        """Check for new database additions and send welcome emails."""
        try:
            # Here you would implement your database checking logic
            # For now, we'll use a mock implementation
            new_contacts = await self.get_new_contacts()
            
            for contact in new_contacts:
                # Add contact to welcome sequence
                self.sequence_manager.add_contact_to_sequence(
                    contact_id=contact['email'],
                    sequence_id="welcome",
                    custom_data={
                        'name': contact['name'],
                        'company': contact.get('company', ''),
                        'signup_date': datetime.now().isoformat()
                    }
                )
                logger.info(f"Added {contact['email']} to welcome sequence")
        
        except Exception as e:
            logger.error(f"Error processing database additions: {str(e)}")
    
    async def get_new_contacts(self) -> List[Dict]:
        """Get new contacts from the database.
        
        This is a mock implementation. Replace with your actual database logic.
        """
        # Mock implementation - replace with your database query
        return []
    
    async def run_scheduled_tasks(self):
        """Run scheduled tasks at regular intervals."""
        self.running = True
        
        def handle_shutdown(signum, frame):
            logger.info("Received shutdown signal")
            self.running = False
        
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        while self.running:
            try:
                logger.info("Running scheduled tasks...")
                
                # Process new database additions
                await self.process_database_additions()
                
                # Process email sequences
                await self.sequence_manager.process_sequences()
                
                # Generate and store analytics
                report = self.analytics.get_analytics_report()
                with open('analytics_report.json', 'w') as f:
                    json.dump(report, f, indent=2)
                
                logger.info("Scheduled tasks completed successfully")
                
            except Exception as e:
                logger.error(f"Error in scheduled tasks: {str(e)}")
            
            await asyncio.sleep(self.check_interval)

async def main():
    """Main function to run the scheduled task manager."""
    task_manager = ScheduledTaskManager()
    await task_manager.run_scheduled_tasks()

if __name__ == "__main__":
    asyncio.run(main())
