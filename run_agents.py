import os
import time
import logging
import asyncio
from datetime import datetime
from agents.list_building_agent import ListBuildingAgent
from agents.asana_manager import AsanaManager
from agents.social_media_manager import SocialMediaManager
from agents.gmb_manager import GMBManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('run_agents.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('RunAgents')

async def run_agents():
    """Run all agents in coordination"""
    try:
        # Initialize agents
        list_builder = ListBuildingAgent()
        asana_manager = AsanaManager()
        social_media = SocialMediaManager()
        gmb_manager = GMBManager()
        
        logger.info("Starting agents...")
        
        while True:
            try:
                start_time = time.time()
                
                # Run list building agent with timeout
                logger.info("Running list building agent...")
                await list_builder.run()
                
                # Update Asana with new agents
                logger.info("Updating Asana with new agents...")
                asana_manager.process_new_agents()
                
                # Run social media campaigns
                logger.info("Running social media campaigns...")
                social_media.create_content_calendar()
                
                # Analyze social media performance
                logger.info("Analyzing social media performance...")
                metrics = social_media.analyze_performance()
                
                # Run GMB optimization
                logger.info("Running GMB optimization...")
                gmb_manager.run_optimization()
                
                # Log status and cleanup
                logger.info("Agent cycle completed. Cleaning up resources...")
                await list_builder.cleanup()
                
                # Calculate remaining sleep time
                elapsed_time = time.time() - start_time
                sleep_time = max(0, (4 * 60 * 60) - elapsed_time)  # 4 hours minus elapsed time
                
                logger.info(f"Waiting {sleep_time/3600:.2f} hours for next cycle...")
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in agent cycle: {str(e)}")
                # Ensure cleanup on error
                try:
                    await list_builder.cleanup()
                except:
                    pass
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
                continue
    
    except KeyboardInterrupt:
        logger.info("Stopping agents...")
        # Cleanup on keyboard interrupt
        try:
            await list_builder.cleanup()
        except:
            pass
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_agents())
