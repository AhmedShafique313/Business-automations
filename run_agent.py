import sys
import asyncio
import logging
from agents.list_building_agent import ListBuildingAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_run.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AgentRunner')

async def main():
    try:
        logger.info("Starting List Building Agent...")
        agent = ListBuildingAgent()
        await agent.run()
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
    finally:
        logger.info("Agent run completed")

if __name__ == "__main__":
    asyncio.run(main())
