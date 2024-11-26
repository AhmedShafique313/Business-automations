"""
Content Agent
Specialized agent for content creation and management.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json

from ..core.base_agent import BaseAgent
from ..core.agent_registry import AgentRegistry
from .processors.content_processor import ContentProcessor

class ContentAgent(BaseAgent):
    """Agent for managing content creation and distribution."""
    
    def __init__(
        self,
        agent_id: str,
        work_dir: str,
        config: Dict,
        registry: AgentRegistry
    ):
        """Initialize the content agent."""
        super().__init__(
            agent_id=agent_id,
            agent_type='content',
            work_dir=work_dir,
            config=config,
            registry=registry
        )
        
        # Initialize content-specific directories
        self.content_dir = self.work_dir / 'content'
        self.content_dir.mkdir(exist_ok=True)
        
        self.templates_dir = self.work_dir / 'templates'
        self.templates_dir.mkdir(exist_ok=True)
        
        # Initialize processor
        self.processor = ContentProcessor(self.templates_dir)
        
        # Load templates
        self.templates = self.load_templates()
    
    def load_templates(self) -> Dict:
        """Load content templates."""
        try:
            template_file = self.templates_dir / 'content_templates.json'
            if template_file.exists():
                with open(template_file) as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load templates: {str(e)}")
            return {}
    
    async def on_start(self):
        """Initialize content agent on startup."""
        try:
            self.logger.info("Starting content agent")
            
            # Load any pending content tasks
            await self.load_pending_tasks()
            
            # Initialize content processors
            await self.initialize_processors()
            
            self.logger.info("Content agent started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start content agent: {str(e)}")
            raise
    
    async def on_stop(self):
        """Cleanup on agent stop."""
        try:
            self.logger.info("Stopping content agent")
            
            # Save current state
            await self.save_state()
            
            # Clean up processors
            await self.cleanup_processors()
            
            self.logger.info("Content agent stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop content agent: {str(e)}")
            raise
    
    async def handle_message(self, message: Dict):
        """Handle incoming content-related messages."""
        try:
            message_type = message.get('type')
            
            if message_type == 'create_content':
                await self.create_content(message['data'])
            elif message_type == 'review_content':
                await self.review_content(message['data'])
            elif message_type == 'distribute_content':
                await self.distribute_content(message['data'])
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle message: {str(e)}")
            raise
    
    async def check_health(self) -> bool:
        """Check content agent health."""
        try:
            # Check directories
            if not self.content_dir.exists() or not self.templates_dir.exists():
                return False
            
            # Check template access
            if not self.templates:
                await self.load_templates()
            
            # Check processor health
            if not await self.check_processor_health():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
    
    async def create_content(self, data: Dict):
        """Create new content based on request."""
        try:
            content_type = data.get('content_type')
            template = self.templates.get(content_type)
            
            if not template:
                raise ValueError(f"No template found for content type: {content_type}")
            
            # Generate content
            content = await self.generate_content(template, data)
            
            # Save content
            content_file = self.save_content(content, content_type)
            
            # Notify completion
            await self.send_message(
                data['requester'],
                {
                    'type': 'content_created',
                    'data': {
                        'content_id': content_file.stem,
                        'content_type': content_type,
                        'status': 'completed'
                    }
                }
            )
            
            self.logger.info(f"Content created successfully: {content_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to create content: {str(e)}")
            # Notify error
            await self.send_message(
                data['requester'],
                {
                    'type': 'content_created',
                    'data': {
                        'status': 'error',
                        'error': str(e)
                    }
                }
            )
            raise
    
    async def review_content(self, data: Dict):
        """Review and validate content."""
        try:
            content_id = data.get('content_id')
            content_file = self.content_dir / f"{content_id}.json"
            
            if not content_file.exists():
                raise ValueError(f"Content not found: {content_id}")
            
            # Load content
            content = self.load_work(content_file)
            
            # Perform review
            review_result = await self.perform_review(content)
            
            # Save review
            review_file = self.save_work(review_result, 'review')
            
            # Notify completion
            await self.send_message(
                data['requester'],
                {
                    'type': 'content_reviewed',
                    'data': {
                        'content_id': content_id,
                        'review_id': review_file.stem,
                        'status': 'completed',
                        'result': review_result['summary']
                    }
                }
            )
            
            self.logger.info(f"Content review completed: {content_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to review content: {str(e)}")
            # Notify error
            await self.send_message(
                data['requester'],
                {
                    'type': 'content_reviewed',
                    'data': {
                        'content_id': content_id,
                        'status': 'error',
                        'error': str(e)
                    }
                }
            )
            raise
    
    async def distribute_content(self, data: Dict):
        """Distribute content to specified channels."""
        try:
            content_id = data.get('content_id')
            channels = data.get('channels', [])
            
            content_file = self.content_dir / f"{content_id}.json"
            if not content_file.exists():
                raise ValueError(f"Content not found: {content_id}")
            
            # Load content
            content = self.load_work(content_file)
            
            # Distribute to each channel
            results = []
            for channel in channels:
                result = await self.distribute_to_channel(content, channel)
                results.append(result)
            
            # Save distribution results
            distribution = {
                'content_id': content_id,
                'timestamp': datetime.now().isoformat(),
                'channels': results
            }
            distribution_file = self.save_work(distribution, 'distribution')
            
            # Notify completion
            await self.send_message(
                data['requester'],
                {
                    'type': 'content_distributed',
                    'data': {
                        'content_id': content_id,
                        'distribution_id': distribution_file.stem,
                        'status': 'completed',
                        'results': results
                    }
                }
            )
            
            self.logger.info(f"Content distributed successfully: {content_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to distribute content: {str(e)}")
            # Notify error
            await self.send_message(
                data['requester'],
                {
                    'type': 'content_distributed',
                    'data': {
                        'content_id': content_id,
                        'status': 'error',
                        'error': str(e)
                    }
                }
            )
            raise
    
    # Helper methods
    
    async def generate_content(self, template: Dict, data: Dict) -> Dict:
        """Generate content using template and data."""
        try:
            content_type = data.get('content_type')
            parameters = data.get('parameters', {})
            
            # Generate content using processor
            content = self.processor.generate_content(content_type, parameters)
            
            # Process content for delivery
            processed_content = self.processor.process_content(content, content_type)
            
            return processed_content
        except Exception as e:
            self.logger.error(f"Failed to generate content: {str(e)}")
            raise
    
    def save_content(self, content: Dict, content_type: str) -> Path:
        """Save content to file."""
        try:
            timestamp = datetime.now().isoformat()
            content_file = self.content_dir / f"{content_type}_{timestamp}.json"
            
            with open(content_file, 'w') as f:
                json.dump(content, f, indent=2)
            
            return content_file
            
        except Exception as e:
            self.logger.error(f"Failed to save content: {str(e)}")
            raise
    
    async def perform_review(self, content: Dict) -> Dict:
        """Perform content review."""
        try:
            # TODO: Implement actual review logic
            review = {
                'content_id': content.get('id'),
                'timestamp': datetime.now().isoformat(),
                'checks': {
                    'quality': True,
                    'compliance': True,
                    'seo': True
                },
                'summary': 'Content meets all requirements'
            }
            return review
        except Exception as e:
            self.logger.error(f"Failed to perform review: {str(e)}")
            raise
    
    async def distribute_to_channel(self, content: Dict, channel: str) -> Dict:
        """Distribute content to a specific channel."""
        try:
            # TODO: Implement actual distribution logic
            result = {
                'channel': channel,
                'timestamp': datetime.now().isoformat(),
                'status': 'success',
                'url': f"https://example.com/{channel}/content"
            }
            return result
        except Exception as e:
            self.logger.error(f"Failed to distribute to channel {channel}: {str(e)}")
            raise
    
    async def initialize_processors(self):
        """Initialize content processors."""
        try:
            # TODO: Initialize actual processors
            self.logger.info("Content processors initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize processors: {str(e)}")
            raise
    
    async def cleanup_processors(self):
        """Clean up content processors."""
        try:
            # TODO: Clean up actual processors
            self.logger.info("Content processors cleaned up")
        except Exception as e:
            self.logger.error(f"Failed to clean up processors: {str(e)}")
            raise
    
    async def check_processor_health(self) -> bool:
        """Check health of content processors."""
        try:
            # TODO: Implement actual processor health checks
            return True
        except Exception as e:
            self.logger.error(f"Processor health check failed: {str(e)}")
            return False
    
    async def load_pending_tasks(self):
        """Load any pending content tasks."""
        try:
            # TODO: Implement pending task loading
            self.logger.info("No pending tasks found")
        except Exception as e:
            self.logger.error(f"Failed to load pending tasks: {str(e)}")
            raise
    
    async def save_state(self):
        """Save current agent state."""
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'templates': self.templates,
                'status': 'stopped'
            }
            state_file = self.work_dir / 'agent_state.json'
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            self.logger.info("Agent state saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save agent state: {str(e)}")
            raise
