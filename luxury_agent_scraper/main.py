import os
import asyncio
import logging
from dotenv import load_dotenv
from models import OpenAIInterface
from agents.list_building_agent import ListBuildingAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI interface
        model_interface = OpenAIInterface()
        
        # Initialize agent
        agent = ListBuildingAgent(model_interface)
        
        # Define target locations
        locations = [
            'Toronto', 'Mississauga', 'Oakville',
            'Richmond Hill', 'Markham', 'Vaughan'
        ]
        
        # Run agent for each location
        for location in locations:
            try:
                logger.info(f"Starting agent discovery for {location}")
                agents_data = await agent.discover_agents(location)
                logger.info(f"Found {len(agents_data)} agents in {location}")
            except Exception as e:
                logger.error(f"Error processing location {location}: {str(e)}")
                continue
        
        logger.info("Agent discovery completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
