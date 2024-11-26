import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import asyncio
from models.model_interface import ModelInterface
from asana_manager import AsanaManager
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential

class CampaignMetrics:
    def __init__(self):
        self.open_rate = 0.0
        self.response_rate = 0.0
        self.conversion_rate = 0.0
        self.sentiment_score = 0.0
        self.engagement_score = 0.0
        self.best_time_of_day = None
        self.best_day_of_week = None
        self.successful_templates = []
        self.unsuccessful_templates = []

class BaseCampaignManager(ABC):
    def __init__(self, campaign_type: str):
        self.campaign_type = campaign_type
        self.setup_logging()
        self.model_interface = ModelInterface()
        self.asana_manager = AsanaManager()
        self.metrics = CampaignMetrics()
        self.learning_data = pd.DataFrame()
        
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{self.campaign_type}_campaign.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f'{self.campaign_type.capitalize()}CampaignManager')

    async def optimize_campaign(self, agent_data: Dict, previous_interactions: List[Dict]) -> Dict:
        """Optimize campaign parameters based on learning data"""
        try:
            # Update learning data with new interactions
            self._update_learning_data(previous_interactions)
            
            # Get personality-based optimization
            personality_params = await self.model_interface.analyze_personality(agent_data)
            
            # Combine ML insights with personality analysis
            optimization_params = {
                'best_time': self._get_optimal_time(),
                'best_day': self._get_optimal_day(),
                'message_style': personality_params.get('communication_style', 'professional'),
                'template_type': self._get_best_template_type(),
                'frequency': self._get_optimal_frequency(),
                'personalization_level': personality_params.get('personalization_preference', 'medium')
            }
            
            return optimization_params
            
        except Exception as e:
            self.logger.error(f"Error optimizing campaign: {str(e)}")
            return {}

    def _update_learning_data(self, interactions: List[Dict]):
        """Update learning dataset with new interaction data"""
        try:
            for interaction in interactions:
                interaction_data = {
                    'timestamp': interaction.get('timestamp'),
                    'day_of_week': pd.to_datetime(interaction.get('timestamp')).dayofweek,
                    'time_of_day': pd.to_datetime(interaction.get('timestamp')).hour,
                    'template_id': interaction.get('template_id'),
                    'personalization_level': interaction.get('personalization_level'),
                    'message_length': len(interaction.get('message', '')),
                    'response_received': interaction.get('response_received', False),
                    'response_time': interaction.get('response_time'),
                    'sentiment_score': interaction.get('sentiment_score'),
                    'converted': interaction.get('converted', False)
                }
                
                self.learning_data = pd.concat([
                    self.learning_data, 
                    pd.DataFrame([interaction_data])
                ], ignore_index=True)
                
        except Exception as e:
            self.logger.error(f"Error updating learning data: {str(e)}")

    def _get_optimal_time(self) -> str:
        """Determine optimal time to send messages"""
        try:
            if len(self.learning_data) < 10:
                return "10:00"  # Default time if not enough data
                
            # Group by hour and calculate success rate
            hourly_success = self.learning_data.groupby('time_of_day').agg({
                'response_received': 'mean',
                'converted': 'mean'
            })
            
            # Weight response rate and conversion rate
            hourly_success['score'] = (
                hourly_success['response_received'] * 0.4 + 
                hourly_success['converted'] * 0.6
            )
            
            best_hour = hourly_success['score'].idxmax()
            return f"{best_hour:02d}:00"
            
        except Exception as e:
            self.logger.error(f"Error getting optimal time: {str(e)}")
            return "10:00"

    def _get_optimal_day(self) -> str:
        """Determine optimal day of week"""
        try:
            if len(self.learning_data) < 10:
                return "Monday"  # Default day if not enough data
                
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            daily_success = self.learning_data.groupby('day_of_week').agg({
                'response_received': 'mean',
                'converted': 'mean'
            })
            
            daily_success['score'] = (
                daily_success['response_received'] * 0.4 + 
                daily_success['converted'] * 0.6
            )
            
            best_day_idx = daily_success['score'].idxmax()
            return days[best_day_idx]
            
        except Exception as e:
            self.logger.error(f"Error getting optimal day: {str(e)}")
            return "Monday"

    def _get_best_template_type(self) -> str:
        """Determine most successful template type"""
        try:
            if len(self.learning_data) < 10:
                return "professional"  # Default template if not enough data
                
            template_success = self.learning_data.groupby('template_id').agg({
                'response_received': 'mean',
                'converted': 'mean',
                'sentiment_score': 'mean'
            })
            
            template_success['score'] = (
                template_success['response_received'] * 0.3 + 
                template_success['converted'] * 0.5 +
                template_success['sentiment_score'] * 0.2
            )
            
            return template_success['score'].idxmax()
            
        except Exception as e:
            self.logger.error(f"Error getting best template: {str(e)}")
            return "professional"

    def _get_optimal_frequency(self) -> int:
        """Determine optimal frequency of communication"""
        try:
            if len(self.learning_data) < 10:
                return 7  # Default to weekly if not enough data
                
            # Analyze response rates based on time between messages
            self.learning_data['time_since_last'] = self.learning_data['timestamp'].diff()
            
            frequency_success = self.learning_data.groupby(
                pd.Grouper(key='time_since_last', freq='D')
            ).agg({
                'response_received': 'mean',
                'converted': 'mean'
            })
            
            frequency_success['score'] = (
                frequency_success['response_received'] * 0.4 + 
                frequency_success['converted'] * 0.6
            )
            
            optimal_days = frequency_success['score'].idxmax().days
            return max(3, min(optimal_days, 14))  # Keep between 3 and 14 days
            
        except Exception as e:
            self.logger.error(f"Error getting optimal frequency: {str(e)}")
            return 7

    @abstractmethod
    async def send_message(self, agent_data: Dict, message: str) -> bool:
        """Send message through specific channel"""
        pass

    @abstractmethod
    async def process_response(self, response_data: Dict) -> Dict:
        """Process response from specific channel"""
        pass

    async def update_task(self, task_gid: str, interaction_data: Dict):
        """Update Asana task with interaction details"""
        try:
            await self.asana_manager.add_interaction(task_gid, {
                'type': self.campaign_type,
                'channel': self.campaign_type.lower(),
                'status': interaction_data.get('status', 'sent'),
                'details': interaction_data.get('message', ''),
                'response': interaction_data.get('response', ''),
                'next_steps': interaction_data.get('next_steps', [])
            })
        except Exception as e:
            self.logger.error(f"Error updating task: {str(e)}")

    async def analyze_response(self, response_text: str) -> Dict:
        """Analyze response sentiment and content"""
        try:
            analysis = await self.model_interface.analyze_response({
                'text': response_text,
                'campaign_type': self.campaign_type
            })
            
            return {
                'sentiment': analysis.get('sentiment', 0),
                'intent': analysis.get('intent', 'unknown'),
                'key_points': analysis.get('key_points', []),
                'suggested_followup': analysis.get('suggested_followup', '')
            }
        except Exception as e:
            self.logger.error(f"Error analyzing response: {str(e)}")
            return {}
