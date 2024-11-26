"""
Enhanced Agent Orchestrator
Manages the lifecycle and coordination of all agents in the system.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from .agent_registry import AgentRegistry
from .base_agent import BaseAgent

class AgentOrchestrator:
    """Manages and coordinates all agents in the system."""
    
    def __init__(self, work_dir: str):
        """Initialize the orchestrator."""
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger('AgentOrchestrator')
        self.setup_logging()
        
        # Initialize registry
        self.registry = AgentRegistry(work_dir)
        
        # Track running tasks
        self.tasks: Dict[str, asyncio.Task] = {}
        
        self.logger.info("Agent orchestrator initialized")
    
    def setup_logging(self):
        """Set up orchestrator logging."""
        log_file = self.work_dir / 'orchestrator.log'
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    async def start_agent(self, agent: BaseAgent):
        """Start an agent and monitor its lifecycle."""
        try:
            self.logger.info(f"Starting agent {agent.agent_id}")
            
            # Start the agent
            await agent.start()
            
            # Create monitoring task
            task = asyncio.create_task(self.monitor_agent(agent))
            self.tasks[agent.agent_id] = task
            
            self.logger.info(f"Agent {agent.agent_id} started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start agent {agent.agent_id}: {str(e)}")
            raise
    
    async def stop_agent(self, agent_id: str):
        """Stop an agent."""
        try:
            self.logger.info(f"Stopping agent {agent_id}")
            
            # Get agent state
            state = self.registry.get_agent_state(agent_id)
            if state.status not in ['running', 'error']:
                self.logger.warning(f"Agent {agent_id} is not running")
                return
            
            # Get agent instance
            agent = self.registry.get_agent_instance(agent_id)
            
            # Stop the agent
            await agent.stop()
            
            # Cancel monitoring task
            if agent_id in self.tasks:
                self.tasks[agent_id].cancel()
                del self.tasks[agent_id]
            
            self.logger.info(f"Agent {agent_id} stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop agent {agent_id}: {str(e)}")
            raise
    
    async def monitor_agent(self, agent: BaseAgent):
        """Monitor an agent's health and status."""
        try:
            while True:
                # Get latest state
                state = self.registry.get_agent_state(agent.agent_id)
                
                # Check if agent needs recovery
                if state.health == 'unhealthy':
                    self.logger.warning(f"Agent {agent.agent_id} is unhealthy, attempting recovery")
                    await self.recover_agent(agent.agent_id)
                
                await asyncio.sleep(60)  # Check every minute
                
        except asyncio.CancelledError:
            self.logger.info(f"Stopped monitoring agent {agent.agent_id}")
        except Exception as e:
            self.logger.error(f"Error monitoring agent {agent.agent_id}: {str(e)}")
    
    async def recover_agent(self, agent_id: str):
        """Attempt to recover a failed agent."""
        try:
            self.logger.info(f"Attempting to recover agent {agent_id}")
            
            # Stop the agent
            await self.stop_agent(agent_id)
            
            # Get agent instance
            agent = self.registry.get_agent_instance(agent_id)
            
            # Restart the agent
            await self.start_agent(agent)
            
            # Verify health
            state = self.registry.get_agent_state(agent_id)
            if state.health == 'healthy':
                self.logger.info(f"Successfully recovered agent {agent_id}")
            else:
                raise ValueError(f"Failed to recover agent {agent_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to recover agent {agent_id}: {str(e)}")
            raise
    
    async def start_all_agents(self):
        """Start all registered agents."""
        try:
            self.logger.info("Starting all agents")
            
            for agent_id in self.registry.get_all_agents():
                agent = self.registry.get_agent_instance(agent_id)
                await self.start_agent(agent)
            
            self.logger.info("All agents started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start all agents: {str(e)}")
            raise
    
    async def stop_all_agents(self):
        """Stop all running agents."""
        try:
            self.logger.info("Stopping all agents")
            
            for agent_id in list(self.tasks.keys()):
                await self.stop_agent(agent_id)
            
            self.logger.info("All agents stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop all agents: {str(e)}")
            raise
    
    async def health_check(self):
        """Perform health check on all agents."""
        try:
            self.logger.info("Starting health check")
            await self.registry.health_check()
            self.logger.info("Health check completed")
            
        except Exception as e:
            self.logger.error(f"Failed to perform health check: {str(e)}")
            raise
    
    def get_agent_status(self, agent_id: str) -> Dict:
        """Get the current status of an agent."""
        return self.registry.get_agent_state(agent_id)
    
    def get_all_agent_status(self) -> Dict[str, Dict]:
        """Get status of all agents."""
        return self.registry.get_all_agents()
