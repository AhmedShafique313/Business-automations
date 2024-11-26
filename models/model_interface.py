import os
import logging
import json
from typing import Dict, List, Optional, Union
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

class ModelInterface:
    """Interface for interacting with language models"""
    
    def __init__(self):
        """Initialize the model interface"""
        self.setup_logging()
        self._load_credentials()
        
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('model_interface.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ModelInterface')

    def _load_credentials(self):
        """Load OpenAI credentials"""
        try:
            with open('agents/credentials.json', 'r') as f:
                creds = json.load(f)
                openai.api_key = creds['OPENAI']['api_key']
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_response(self, prompt: str) -> str:
        """Generate a response using OpenAI"""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a luxury real estate expert assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise

    async def _call_openai(self, prompt: str) -> str:
        """Generate a response using OpenAI"""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a luxury real estate expert assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise

    async def analyze_agent(self, agent_data: Dict) -> Dict:
        """Analyze agent data using the model"""
        try:
            # Create a prompt for agent analysis
            prompt = f"""
            Analyze this luxury real estate agent's profile and respond in JSON format:
            
            Name: {agent_data.get('name', 'Unknown')}
            Brokerage: {agent_data.get('brokerage', 'Unknown')}
            Location: {agent_data.get('location', 'Unknown')}
            Description: {agent_data.get('description', '')}
            
            Analyze the profile and return a JSON object with these exact keys:
            {{
                "luxury_score": (0-100 integer indicating likelihood this is a luxury agent),
                "strengths": [list of key strengths and specialties],
                "target_market": (description of target market),
                "price_range": (estimated price range they work in),
                "marketing_suggestions": [list of marketing approach suggestions],
                "collaboration_opportunities": (potential collaboration opportunities)
            }}
            
            Respond ONLY with the JSON object, no other text.
            """
            
            response = await self.generate_response(prompt)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse model response as JSON")
                return {"luxury_score": 0}
                
        except Exception as e:
            self.logger.error(f"Error analyzing agent: {str(e)}")
            return {"luxury_score": 0}

    async def analyze_social_content(self, social_data: Dict) -> Dict:
        """Analyze social media content and engagement patterns"""
        prompt = f"""
        Analyze the following social media data and provide insights about content patterns and engagement:
        {json.dumps(social_data, indent=2)}
        
        Focus on:
        1. Content themes and topics
        2. Posting frequency and timing
        3. Engagement rates and patterns
        4. Professional vs personal content ratio
        5. Communication style and tone
        
        Return a JSON object with the following structure:
        {{
            "content_focus": "Main themes and topics",
            "post_frequency": "Posting frequency pattern",
            "engagement_rate": "Average engagement rate",
            "content_style": "Description of content style",
            "key_observations": ["List of important observations"]
        }}
        """
        
        try:
            response = await self._call_openai(prompt)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Error analyzing social content: {str(e)}")
            return {}

    async def analyze_personality(self, analysis_data: Dict) -> Dict:
        """Analyze agent's personality and communication preferences"""
        prompt = f"""
        Based on the following agent data, analyze their personality and communication style:
        {json.dumps(analysis_data, indent=2)}
        
        Consider:
        1. Communication style (formal vs casual)
        2. Professional approach
        3. Values and priorities
        4. Decision-making style
        5. Relationship building approach
        
        Return a JSON object with:
        {{
            "personality_type": "MBTI-style personality type",
            "communication_style": "Preferred communication approach",
            "key_traits": ["List of dominant personality traits"],
            "preferred_contact": "Best channel for communication",
            "relationship_building": "How to build rapport",
            "decision_factors": ["Key factors in their decision making"]
        }}
        """
        
        try:
            response = await self._call_openai(prompt)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Error analyzing personality: {str(e)}")
            return {}

    async def analyze_market_presence(self, market_data: Dict) -> Dict:
        """Analyze agent's market presence and activity patterns"""
        prompt = f"""
        Analyze the following market presence data:
        {json.dumps(market_data, indent=2)}
        
        Focus on:
        1. Market positioning
        2. Target client segment
        3. Geographic focus
        4. Price point specialization
        5. Property type preferences
        
        Return a JSON object with:
        {{
            "market_position": "Description of market position",
            "target_market": "Primary client segment",
            "price_range": "Typical price range",
            "specialties": ["List of specializations"],
            "market_share": "Estimated market presence"
        }}
        """
        
        try:
            response = await self._call_openai(prompt)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Error analyzing market presence: {str(e)}")
            return {}

    async def create_engagement_strategy(self, strategy_data: Dict) -> Dict:
        """Create personalized engagement strategy based on agent analysis"""
        prompt = f"""
        Create a personalized engagement strategy based on this data:
        {json.dumps(strategy_data, indent=2)}
        
        Consider:
        1. Personality type and communication preferences
        2. Professional goals and priorities
        3. Market position and target segment
        4. Social media presence and engagement patterns
        5. Current market activities
        
        Return a JSON object with:
        {{
            "strategy": "Detailed engagement strategy",
            "communication_channels": ["Prioritized list of channels"],
            "messaging_approach": "How to frame messages",
            "content_strategy": "Content themes and types",
            "frequency": "Contact frequency recommendation",
            "action_items": ["Specific next steps"],
            "success_metrics": ["KPIs to track"]
        }}
        """
        
        try:
            response = await self._call_openai(prompt)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Error creating engagement strategy: {str(e)}")
            return {}
