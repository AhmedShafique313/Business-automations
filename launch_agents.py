#!/usr/bin/env python3
"""
Launch script for Design Gaga Business Development System
Starts the agents in perpetual operation mode.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

from agents.agent_orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agents.log')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Set up working directory
        work_dir = Path(os.getenv('WORK_DIR', 'agents/work'))
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize and start orchestrator
        logger.info("Initializing Agent Orchestrator...")
        orchestrator = AgentOrchestrator()
        
        logger.info("Starting perpetual operation mode...")
        await orchestrator.run_perpetual()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, gracefully stopping agents...")
        await orchestrator.shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete.")
