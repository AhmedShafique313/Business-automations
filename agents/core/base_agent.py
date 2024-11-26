"""
Enhanced Base Agent
Provides core functionality for all agents in the system.
"""

import os
import logging
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any
from abc import ABC, abstractmethod

from .agent_registry import AgentRegistry

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        work_dir: str,
        config: Dict,
        registry: AgentRegistry
    ):
        """Initialize the base agent."""
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.work_dir = Path(work_dir) / agent_id
        self.config = config
        self.registry = registry
        
        # Create work directory
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger(f"{agent_type}.{agent_id}")
        self.setup_logging()
        
        # Register with registry
        self.state = self.registry.register_agent(
            agent_id=agent_id,
            agent_type=agent_type,
            config=config
        )
        
        # Initialize message queue
        self.message_queue = asyncio.Queue()
        
        self.logger.info(f"Agent {agent_id} initialized")
    
    def setup_logging(self):
        """Set up agent-specific logging."""
        log_file = self.work_dir / f'{self.agent_id}.log'
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    async def start(self):
        """Start the agent."""
        try:
            self.logger.info("Starting agent")
            
            # Update state
            self.state = self.registry.update_agent_state(
                self.agent_id,
                status='running',
                health='healthy'
            )
            
            # Start message processing
            asyncio.create_task(self.process_messages())
            
            # Start health check
            asyncio.create_task(self.health_check_loop())
            
            # Call agent-specific startup
            await self.on_start()
            
            self.logger.info("Agent started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start agent: {str(e)}")
            self.registry.update_agent_state(
                self.agent_id,
                status='error',
                health='unhealthy',
                metrics={'errors': self.state.metrics['errors'] + 1}
            )
            raise
    
    async def stop(self):
        """Stop the agent."""
        try:
            self.logger.info("Stopping agent")
            
            # Call agent-specific cleanup
            await self.on_stop()
            
            # Update state
            self.state = self.registry.update_agent_state(
                self.agent_id,
                status='stopped'
            )
            
            self.logger.info("Agent stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop agent: {str(e)}")
            self.registry.update_agent_state(
                self.agent_id,
                status='error',
                health='unhealthy',
                metrics={'errors': self.state.metrics['errors'] + 1}
            )
            raise
    
    async def process_messages(self):
        """Process messages from the queue."""
        while True:
            try:
                message = await self.message_queue.get()
                
                # Update metrics
                self.state = self.registry.update_agent_state(
                    self.agent_id,
                    metrics={
                        'messages_processed': self.state.metrics['messages_processed'] + 1,
                        'last_active': datetime.now().isoformat()
                    }
                )
                
                # Process message
                await self.handle_message(message)
                
                self.message_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
                self.registry.update_agent_state(
                    self.agent_id,
                    health='unhealthy',
                    metrics={'errors': self.state.metrics['errors'] + 1}
                )
    
    async def send_message(self, target_agent: str, message: Dict):
        """Send a message to another agent."""
        try:
            # Get target agent
            target_state = self.registry.get_agent_state(target_agent)
            if target_state.status != 'running':
                raise ValueError(f"Target agent {target_agent} is not running")
            
            # Add message metadata
            message['source'] = self.agent_id
            message['timestamp'] = datetime.now().isoformat()
            
            # Save message for debugging
            message_file = self.work_dir / 'messages' / f'outgoing_{datetime.now().isoformat()}.json'
            message_file.parent.mkdir(exist_ok=True)
            with open(message_file, 'w') as f:
                json.dump(message, f, indent=2)
            
            # Send message
            target_agent_instance = self.registry.get_agent_instance(target_agent)
            await target_agent_instance.message_queue.put(message)
            
            self.logger.info(f"Sent message to {target_agent}")
            
        except Exception as e:
            self.logger.error(f"Failed to send message to {target_agent}: {str(e)}")
            raise
    
    def save_work(self, work_item: Any, category: str) -> Path:
        """Save work items to JSON file."""
        try:
            timestamp = datetime.now().isoformat()
            work_file = self.work_dir / 'work' / f'{category}_{timestamp}.json'
            work_file.parent.mkdir(exist_ok=True)
            
            with open(work_file, 'w') as f:
                json.dump({
                    'agent_id': self.agent_id,
                    'agent_type': self.agent_type,
                    'timestamp': timestamp,
                    'category': category,
                    'content': work_item
                }, f, indent=2)
            
            return work_file
            
        except Exception as e:
            self.logger.error(f"Failed to save work item: {str(e)}")
            raise
    
    def load_work(self, work_file: Path) -> Dict:
        """Load work items from JSON file."""
        try:
            with open(work_file) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load work item: {str(e)}")
            raise
    
    async def health_check_loop(self):
        """Periodic health check."""
        while True:
            try:
                # Perform agent-specific health check
                healthy = await self.check_health()
                
                # Update state
                self.state = self.registry.update_agent_state(
                    self.agent_id,
                    health='healthy' if healthy else 'unhealthy'
                )
                
            except Exception as e:
                self.logger.error(f"Health check failed: {str(e)}")
                self.registry.update_agent_state(
                    self.agent_id,
                    health='unhealthy',
                    metrics={'errors': self.state.metrics['errors'] + 1}
                )
            
            await asyncio.sleep(60)  # Check every minute
    
    # Abstract methods that must be implemented by derived classes
    
    @abstractmethod
    async def on_start(self):
        """Called when the agent starts."""
        pass
    
    @abstractmethod
    async def on_stop(self):
        """Called when the agent stops."""
        pass
    
    @abstractmethod
    async def handle_message(self, message: Dict):
        """Handle an incoming message."""
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """Perform agent-specific health check."""
        pass
