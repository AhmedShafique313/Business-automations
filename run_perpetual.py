"""
Run the AI Marketing Platform in perpetual mode.
Includes robust error handling and state persistence.
"""

import asyncio
import logging
from pathlib import Path
import signal
import sys
import json
from datetime import datetime
import os
import traceback
from typing import Dict

from agents.agent_orchestrator import AgentOrchestrator

# Configure logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / f'perpetual_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Industries to target
INDUSTRIES = [
    'tech',
    'finance',
    'healthcare',
    'education',
    'ecommerce'
]

# Platforms to use
PLATFORMS = [
    'linkedin',
    'medium',
    'youtube',
    'instagram'
]

# State file for persistence
STATE_FILE = 'perpetual_state.json'

class PerpetualRunner:
    """Runs the AI Marketing Platform continuously."""
    
    def __init__(self):
        """Initialize the perpetual runner."""
        self.orchestrator = AgentOrchestrator()
        self.running = False
        self.state = self._load_state()
        
    def _load_state(self) -> Dict:
        """Load saved state if it exists."""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            return {
                'last_run': None,
                'processed_trends': [],
                'active_campaigns': {},
                'lead_stats': {
                    'total': 0,
                    'qualified': 0,
                    'converted': 0
                }
            }
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {}
            
    def _save_state(self):
        """Save current state to file."""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Shutdown signal received")
        self.running = False
        
    async def run(self):
        """Run the platform continuously."""
        try:
            logger.info("Starting perpetual runner")
            self.running = True
            
            # Initialize agents
            await self.orchestrator.initialize_agents()
            
            while self.running:
                try:
                    # Process each industry
                    for industry in INDUSTRIES:
                        logger.info(f"Processing industry: {industry}")
                        
                        # Analyze trends
                        trends = await self.orchestrator.analyze_industry_trends(industry)
                        
                        # Generate content for each platform
                        for platform in PLATFORMS:
                            if not self.running:
                                break
                                
                            try:
                                logger.info(f"Generating content for {platform}")
                                content = await self.orchestrator.generate_platform_content(
                                    industry=industry,
                                    platform=platform,
                                    trends=trends
                                )
                                
                                # Process any leads generated
                                if content.get('leads'):
                                    for lead in content['leads']:
                                        await self.orchestrator.process_new_lead(lead)
                                        
                            except Exception as e:
                                logger.error(f"Error processing platform {platform}: {e}")
                                continue
                                
                    # Update state
                    self.state['last_run'] = datetime.now().isoformat()
                    self._save_state()
                    
                    # Wait before next iteration
                    await asyncio.sleep(3600)  # 1 hour
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(300)  # 5 minutes on error
                    
        except Exception as e:
            logger.error(f"Critical error in perpetual runner: {e}")
            traceback.print_exc()
        finally:
            self._save_state()
            logger.info("Perpetual runner stopped")
            
    @staticmethod
    async def main():
        """Main entry point."""
        runner = PerpetualRunner()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, runner.signal_handler)
        signal.signal(signal.SIGTERM, runner.signal_handler)
        
        # Run the platform
        await runner.run()

if __name__ == "__main__":
    asyncio.run(PerpetualRunner.main())
