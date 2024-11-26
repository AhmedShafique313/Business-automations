"""
Agent Registry
Manages agent registration, state, and lifecycle.
"""

import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import asyncio

@dataclass
class AgentState:
    """Represents the state of an agent."""
    agent_id: str
    agent_type: str
    status: str  # initialized, running, stopped, error
    health: str  # healthy, unhealthy, unknown
    last_update: str
    config: Dict
    metrics: Dict

class AgentRegistry:
    """Central registry for all agents in the system."""
    
    def __init__(self, work_dir: str):
        """Initialize the agent registry."""
        self.work_dir = Path(work_dir)
        self.registry_dir = self.work_dir / 'registry'
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger('AgentRegistry')
        self.setup_logging()
        
        # Load existing registry
        self.agents: Dict[str, AgentState] = {}
        self.load_registry()
    
    def setup_logging(self):
        """Set up logging for the registry."""
        log_file = self.registry_dir / 'registry.log'
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    def load_registry(self):
        """Load the agent registry from disk."""
        try:
            registry_file = self.registry_dir / 'registry.json'
            if registry_file.exists():
                with open(registry_file) as f:
                    data = json.load(f)
                    for agent_id, state_dict in data.items():
                        self.agents[agent_id] = AgentState(**state_dict)
                self.logger.info(f"Loaded {len(self.agents)} agents from registry")
        except Exception as e:
            self.logger.error(f"Failed to load registry: {str(e)}")
    
    def save_registry(self):
        """Save the agent registry to disk."""
        try:
            registry_file = self.registry_dir / 'registry.json'
            with open(registry_file, 'w') as f:
                json.dump(
                    {id: asdict(state) for id, state in self.agents.items()},
                    f,
                    indent=2
                )
            self.logger.info("Registry saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save registry: {str(e)}")
    
    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        config: Dict
    ) -> AgentState:
        """Register a new agent."""
        try:
            if agent_id in self.agents:
                raise ValueError(f"Agent {agent_id} already registered")
            
            state = AgentState(
                agent_id=agent_id,
                agent_type=agent_type,
                status='initialized',
                health='unknown',
                last_update=datetime.now().isoformat(),
                config=config,
                metrics={
                    'messages_processed': 0,
                    'errors': 0,
                    'last_active': datetime.now().isoformat()
                }
            )
            
            self.agents[agent_id] = state
            self.save_registry()
            
            self.logger.info(f"Agent {agent_id} registered successfully")
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent_id}: {str(e)}")
            raise
    
    def update_agent_state(
        self,
        agent_id: str,
        status: Optional[str] = None,
        health: Optional[str] = None,
        metrics: Optional[Dict] = None
    ) -> AgentState:
        """Update the state of an agent."""
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            state = self.agents[agent_id]
            
            if status:
                state.status = status
            if health:
                state.health = health
            if metrics:
                state.metrics.update(metrics)
            
            state.last_update = datetime.now().isoformat()
            self.save_registry()
            
            self.logger.info(f"Updated state for agent {agent_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to update agent {agent_id} state: {str(e)}")
            raise
    
    def get_agent_state(self, agent_id: str) -> AgentState:
        """Get the current state of an agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        return self.agents[agent_id]
    
    def get_all_agents(self) -> Dict[str, AgentState]:
        """Get all registered agents."""
        return self.agents.copy()
    
    def deregister_agent(self, agent_id: str):
        """Remove an agent from the registry."""
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            del self.agents[agent_id]
            self.save_registry()
            
            self.logger.info(f"Agent {agent_id} deregistered successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to deregister agent {agent_id}: {str(e)}")
            raise
    
    async def health_check(self):
        """Perform health check on all registered agents."""
        try:
            self.logger.info("Starting health check")
            
            for agent_id, state in self.agents.items():
                try:
                    if state.status == 'running':
                        # Check agent directory
                        agent_dir = self.work_dir / agent_id
                        if not agent_dir.exists():
                            self.update_agent_state(
                                agent_id,
                                health='unhealthy',
                                metrics={'errors': state.metrics['errors'] + 1}
                            )
                            continue
                        
                        # Check last update time
                        last_update = datetime.fromisoformat(state.last_update)
                        if (datetime.now() - last_update).total_seconds() > 300:  # 5 minutes
                            self.update_agent_state(
                                agent_id,
                                health='unhealthy',
                                metrics={'errors': state.metrics['errors'] + 1}
                            )
                            continue
                        
                        self.update_agent_state(agent_id, health='healthy')
                        
                except Exception as e:
                    self.logger.error(f"Health check failed for agent {agent_id}: {str(e)}")
                    self.update_agent_state(
                        agent_id,
                        health='unhealthy',
                        metrics={'errors': state.metrics['errors'] + 1}
                    )
            
            self.logger.info("Health check completed")
            
        except Exception as e:
            self.logger.error(f"Failed to perform health check: {str(e)}")
            raise
