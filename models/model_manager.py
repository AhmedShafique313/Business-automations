import os
import logging
from typing import Dict, List, Optional, Union
from browser_use import BrowserUse
from browser_use.models import Model

class ModelManager:
    """Manages GPT-4O and GPT-4O Mini model interactions"""
    
    def __init__(self):
        """Initialize the model manager"""
        self.setup_logging()
        self.browser = BrowserUse()
        self.models = {
            'gpt4o': Model.GPT4O,
            'gpt4o_mini': Model.GPT4O_MINI
        }
        self.current_model = 'gpt4o'  # Default to GPT-4O
        
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('model_manager.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ModelManager')
        
    def set_model(self, model_name: str) -> bool:
        """Set the current model to use"""
        if model_name.lower() not in self.models:
            self.logger.error(f"Invalid model name: {model_name}")
            return False
        self.current_model = model_name.lower()
        self.logger.info(f"Switched to model: {model_name}")
        return True
        
    async def generate_response(self, prompt: str) -> str:
        """Generate a response using the current model"""
        try:
            model = self.models[self.current_model]
            response = await self.browser.generate_response(prompt, model=model)
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return ""
            
    async def analyze_agent(self, agent_data: Dict) -> Dict:
        """Analyze agent data using the current model"""
        try:
            # Create a prompt for agent analysis
            prompt = f"""
            Analyze this luxury real estate agent's profile:
            Name: {agent_data.get('name', 'Unknown')}
            Brokerage: {agent_data.get('brokerage', 'Unknown')}
            Location: {agent_data.get('location', 'Unknown')}
            Description: {agent_data.get('description', '')}
            
            Please provide:
            1. Likelihood this is a luxury agent (0-100%)
            2. Key strengths and specialties
            3. Recommended approach for outreach
            """
            
            response = await self.generate_response(prompt)
            
            # Parse the response into structured data
            analysis = {
                'luxury_score': self._extract_luxury_score(response),
                'strengths': self._extract_strengths(response),
                'outreach_strategy': self._extract_outreach(response)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing agent: {str(e)}")
            return {
                'luxury_score': 0,
                'strengths': [],
                'outreach_strategy': ''
            }
            
    def _extract_luxury_score(self, response: str) -> int:
        """Extract luxury score from model response"""
        try:
            # Look for percentage in the response
            import re
            matches = re.findall(r'(\d+)%', response)
            if matches:
                return min(100, max(0, int(matches[0])))
            return 0
        except:
            return 0
            
    def _extract_strengths(self, response: str) -> List[str]:
        """Extract key strengths from model response"""
        try:
            # Look for bullet points or numbered lists
            strengths = []
            lines = response.split('\n')
            for line in lines:
                if ('•' in line or '-' in line or 
                    any(f"{i}." in line for i in range(10))):
                    strength = line.replace('•', '').replace('-', '').strip()
                    if strength:
                        strengths.append(strength)
            return strengths
        except:
            return []
            
    def _extract_outreach(self, response: str) -> str:
        """Extract outreach strategy from model response"""
        try:
            # Look for outreach or approach related content
            lines = response.split('\n')
            for i, line in enumerate(lines):
                if any(word in line.lower() for word in 
                      ['outreach', 'approach', 'recommend', 'strategy']):
                    return ' '.join(lines[i:i+3])
            return ''
        except:
            return ''
            
    def close(self):
        """Close the browser session"""
        try:
            self.browser.close()
        except:
            pass
