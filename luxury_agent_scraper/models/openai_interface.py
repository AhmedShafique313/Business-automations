import os
import json
import asyncio
from typing import Dict
from openai import AsyncOpenAI
from dotenv import load_dotenv
from utils.errors import APIError

load_dotenv()

class OpenAIInterface:
    def __init__(self):
        """Initialize OpenAI interface"""
        self.client = AsyncOpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.temperature = float(os.getenv('MODEL_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('MODEL_MAX_TOKENS', '500'))
    
    async def analyze_agent(self, agent_data: Dict) -> Dict:
        """
        Analyze agent data using OpenAI
        
        Args:
            agent_data (Dict): Agent data to analyze
            
        Returns:
            Dict: Analysis results
            
        Raises:
            APIError: If API call fails
        """
        try:
            prompt = self._create_analysis_prompt(agent_data)
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a luxury real estate expert analyzing agent profiles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            analysis = response.choices[0].message.content
            analysis_dict = json.loads(analysis)
            
            return {
                'luxury_score': analysis_dict['luxury_score'],
                'analysis': analysis_dict['analysis'],
                'recommendations': analysis_dict['recommendations']
            }
            
        except Exception as e:
            raise APIError(f"OpenAI API error: {str(e)}")
    
    def _create_analysis_prompt(self, agent_data: Dict) -> str:
        """Create prompt for agent analysis"""
        prompt = f"""
        Analyze this luxury real estate agent's profile and provide a detailed assessment.
        Please respond in JSON format with the following structure:
        {{
            "luxury_score": (1-100 score based on luxury market presence),
            "analysis": "detailed analysis of agent's luxury market presence",
            "recommendations": "strategic recommendations for working with this agent"
        }}

        Agent Profile:
        Name: {agent_data.get('name', 'N/A')}
        Brokerage: {agent_data.get('brokerage', 'N/A')}
        Location: {agent_data.get('location', 'N/A')}
        Description: {agent_data.get('description', 'N/A')}
        Website: {agent_data.get('website_url', 'N/A')}
        LinkedIn: {agent_data.get('linkedin_url', 'N/A')}
        Instagram: {agent_data.get('instagram_handle', 'N/A')}
        Facebook: {agent_data.get('facebook_handle', 'N/A')}
        Twitter: {agent_data.get('twitter_handle', 'N/A')}
        """
        return prompt
