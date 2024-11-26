#!/usr/bin/env python3

import sys
import traceback
from agents.asana_manager import AsanaManager
import logging
import os
import asana

def main():
    # Set up environment variables
    os.environ['ASANA_ACCESS_TOKEN'] = '1/1208846726385887:a3e2c2a1a81b9a0c8a5c0e4d7f6b9a2d'

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('update_asana_tasks.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger('UpdateAsanaTasks')

    try:
        # Directly use Asana client to test connection
        client = asana.Client.access_token(os.environ['ASANA_ACCESS_TOKEN'])
        
        # Try to get user info to verify connection
        me = client.users.me()
        logger.info(f"Connected as user: {me.get('name', 'Unknown')}")

        # Initialize Asana manager
        logger.info("Initializing Asana manager...")
        manager = AsanaManager()

        # Update all tasks
        logger.info("Starting task update process...")
        success = manager.update_all_tasks()

        if success:
            logger.info("Successfully completed task updates")
        else:
            logger.error("Failed to complete all task updates")

    except Exception as e:
        logger.error(f"Error during task update process: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
