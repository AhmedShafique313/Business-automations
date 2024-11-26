"""
Agent Orchestrator
Manages and coordinates multiple agents for the marketing automation platform.
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime

from .auth.auth_manager import AuthManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Manages and coordinates multiple agents."""
    
    def __init__(self):
        """Initialize the agent orchestrator."""
        self.auth_manager = AuthManager()
        self.agents = {}
        self.agent_status = {}
        self.agent_metrics = {}
        
        # Set up work directory
        self.work_dir = Path(os.getenv('WORK_DIR', '/mnt/VANDAN_DISK/code_stuff/projects/experiments/agents/work'))
        self.work_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize_agent(self, agent_id: str, agent_type: str, config: Dict):
        """Initialize a new agent with given configuration."""
        try:
            logger.info(f"Initializing agent {agent_id} of type {agent_type}")
            
            # Validate agent type
            if agent_type not in ['asana', 'google', 'facebook', 'linkedin']:
                raise ValueError(f"Invalid agent type: {agent_type}")
            
            # Create agent directory
            agent_dir = self.work_dir / agent_id
            agent_dir.mkdir(exist_ok=True)
            
            # Store agent configuration
            config_file = agent_dir / 'config.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Initialize agent status
            self.agent_status[agent_id] = {
                'status': 'initializing',
                'last_update': datetime.now().isoformat(),
                'type': agent_type,
                'health': 'unknown'
            }
            
            # Initialize metrics
            self.agent_metrics[agent_id] = {
                'messages_processed': 0,
                'errors': 0,
                'last_active': datetime.now().isoformat()
            }
            
            logger.info(f"Agent {agent_id} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent {agent_id}: {str(e)}")
            raise
    
    async def start_agent(self, agent_id: str):
        """Start an initialized agent."""
        try:
            logger.info(f"Starting agent {agent_id}")
            
            if agent_id not in self.agent_status:
                raise ValueError(f"Agent {agent_id} not initialized")
            
            # Load agent configuration
            agent_dir = self.work_dir / agent_id
            config_file = agent_dir / 'config.json'
            
            if not config_file.exists():
                raise ValueError(f"Configuration not found for agent {agent_id}")
            
            with open(config_file) as f:
                config = json.load(f)
            
            # Get authentication token
            agent_type = self.agent_status[agent_id]['type']
            token = await self.auth_manager.get_valid_token(agent_type)
            
            # Update agent status
            self.agent_status[agent_id]['status'] = 'running'
            self.agent_status[agent_id]['last_update'] = datetime.now().isoformat()
            
            logger.info(f"Agent {agent_id} started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start agent {agent_id}: {str(e)}")
            self.agent_status[agent_id]['status'] = 'error'
            self.agent_status[agent_id]['health'] = 'unhealthy'
            self.agent_metrics[agent_id]['errors'] += 1
            raise
    
    async def stop_agent(self, agent_id: str):
        """Stop a running agent."""
        try:
            logger.info(f"Stopping agent {agent_id}")
            
            if agent_id not in self.agent_status:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Update agent status
            self.agent_status[agent_id]['status'] = 'stopped'
            self.agent_status[agent_id]['last_update'] = datetime.now().isoformat()
            
            logger.info(f"Agent {agent_id} stopped successfully")
            
        except Exception as e:
            logger.error(f"Failed to stop agent {agent_id}: {str(e)}")
            raise
    
    def get_agent_status(self, agent_id: str) -> Dict:
        """Get the current status of an agent."""
        if agent_id not in self.agent_status:
            raise ValueError(f"Agent {agent_id} not found")
        
        return {
            **self.agent_status[agent_id],
            'metrics': self.agent_metrics[agent_id]
        }
    
    def get_all_agent_status(self) -> Dict[str, Dict]:
        """Get status of all agents."""
        return {
            agent_id: self.get_agent_status(agent_id)
            for agent_id in self.agent_status
        }
    
    async def health_check(self):
        """Perform health check on all agents."""
        try:
            logger.info("Starting health check")
            
            for agent_id, status in self.agent_status.items():
                try:
                    if status['status'] == 'running':
                        # Check if agent is responsive
                        agent_dir = self.work_dir / agent_id
                        if not agent_dir.exists():
                            raise ValueError("Agent directory not found")
                        
                        # Check if token is valid
                        agent_type = status['type']
                        await self.auth_manager.get_valid_token(agent_type)
                        
                        # Update health status
                        self.agent_status[agent_id]['health'] = 'healthy'
                        logger.info(f"Agent {agent_id} is healthy")
                        
                except Exception as e:
                    logger.error(f"Health check failed for agent {agent_id}: {str(e)}")
                    self.agent_status[agent_id]['health'] = 'unhealthy'
                    self.agent_metrics[agent_id]['errors'] += 1
            
        except Exception as e:
            logger.error(f"Failed to perform health check: {str(e)}")
            raise
    
    async def process_message(self, agent_id: str, message: Dict):
        """Process a message using the specified agent."""
        try:
            if agent_id not in self.agent_status:
                raise ValueError(f"Agent {agent_id} not found")
            
            if self.agent_status[agent_id]['status'] != 'running':
                raise ValueError(f"Agent {agent_id} is not running")
            
            logger.info(f"Processing message with agent {agent_id}")
            
            # Update metrics
            self.agent_metrics[agent_id]['messages_processed'] += 1
            self.agent_metrics[agent_id]['last_active'] = datetime.now().isoformat()
            
            # Process message based on agent type
            agent_type = self.agent_status[agent_id]['type']
            
            # Get valid token
            token = await self.auth_manager.get_valid_token(agent_type)
            
            # TODO: Implement actual message processing logic
            logger.info(f"Message processed successfully by agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to process message with agent {agent_id}: {str(e)}")
            self.agent_metrics[agent_id]['errors'] += 1
            raise
    
    async def recover_agent(self, agent_id: str):
        """Attempt to recover a failed agent."""
        try:
            logger.info(f"Attempting to recover agent {agent_id}")
            
            if agent_id not in self.agent_status:
                raise ValueError(f"Agent {agent_id} not found")
            
            if self.agent_status[agent_id]['health'] != 'unhealthy':
                logger.info(f"Agent {agent_id} is already healthy")
                return
            
            # Stop the agent
            await self.stop_agent(agent_id)
            
            # Attempt to restart
            await self.start_agent(agent_id)
            
            # Verify health
            await self.health_check()
            
            if self.agent_status[agent_id]['health'] == 'healthy':
                logger.info(f"Successfully recovered agent {agent_id}")
            else:
                raise ValueError(f"Failed to recover agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to recover agent {agent_id}: {str(e)}")
            raise

if __name__ == "__main__":
    # Set up work directory
    work_dir = Path(os.getenv('WORK_DIR', '/mnt/VANDAN_DISK/code_stuff/projects/experiments/agents/work'))
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize and run orchestrator
    try:
        orchestrator = AgentOrchestrator()
        asyncio.run(orchestrator.health_check())
    except Exception as e:
        logger.error(f"Fatal error in orchestrator: {str(e)}")
        raise
