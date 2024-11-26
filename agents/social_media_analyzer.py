"""Social media analysis and psychological profiling."""
import logging
from typing import Dict, List, Optional
import json
import os
from pathlib import Path
import tweepy
import praw
import openai
from linkedin_api import Linkedin

logger = logging.getLogger(__name__)

class SocialMediaAnalyzer:
    """Analyzes social media content to create psychological profiles."""
    
    def __init__(self, credentials_path: str):
        """Initialize with API credentials."""
        self.setup_logging()
        self.load_credentials(credentials_path)
        self.initialize_apis()
    
    def setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def load_credentials(self, credentials_path: str):
        """Load API credentials from JSON file."""
        with open(credentials_path) as f:
            self.credentials = json.load(f)
        
        # Set up OpenAI for content analysis
        openai.api_key = self.credentials['OPENAI']['api_key']
    
    def initialize_apis(self):
        """Initialize social media API clients."""
        # Twitter API setup
        auth = tweepy.OAuthHandler(
            self.credentials['TWITTER']['consumer_key'],
            self.credentials['TWITTER']['consumer_secret']
        )
        auth.set_access_token(
            self.credentials['TWITTER']['access_token'],
            self.credentials['TWITTER']['access_token_secret']
        )
        self.twitter = tweepy.API(auth)
        
        # Reddit API setup
        self.reddit = praw.Reddit(
            client_id=self.credentials['REDDIT']['client_id'],
            client_secret=self.credentials['REDDIT']['client_secret'],
            user_agent=self.credentials['REDDIT']['user_agent']
        )
        
        # LinkedIn API setup
        self.linkedin = Linkedin(
            self.credentials['LINKEDIN']['username'],
            self.credentials['LINKEDIN']['password']
        )
    
    async def find_social_profiles(self, email: str, name: str) -> Dict[str, str]:
        """Find social media profiles for a given contact."""
        profiles = {}
        
        try:
            # Search Twitter by name
            twitter_users = self.twitter.search_users(name)
            for user in twitter_users[:3]:  # Check first 3 matches
                if self._verify_profile_match(user.description, name, email):
                    profiles['twitter'] = user.screen_name
                    break
            
            # Search Reddit
            reddit_user = self.reddit.redditor(name.replace(' ', '_'))
            try:
                if reddit_user.id:  # Check if user exists
                    profiles['reddit'] = reddit_user.name
            except:
                pass
            
            # Search LinkedIn
            linkedin_results = self.linkedin.search_people(name)
            for profile in linkedin_results:
                if self._verify_profile_match(profile.get('summary', ''), name, email):
                    profiles['linkedin'] = profile['public_id']
                    break
                    
        except Exception as e:
            logger.error(f"Error finding social profiles: {str(e)}")
        
        return profiles
    
    def _verify_profile_match(self, bio: str, name: str, email: str) -> bool:
        """Verify if a social profile matches the contact."""
        # Basic verification - can be enhanced with more sophisticated matching
        name_parts = name.lower().split()
        bio = bio.lower()
        
        return any(part in bio for part in name_parts)
    
    async def analyze_social_content(self, profiles: Dict[str, str]) -> Dict:
        """Analyze social media content to create a psychological profile."""
        content = []
        
        try:
            # Collect Twitter content
            if 'twitter' in profiles:
                tweets = self.twitter.user_timeline(
                    screen_name=profiles['twitter'],
                    count=50,
                    tweet_mode="extended"
                )
                content.extend([tweet.full_text for tweet in tweets])
            
            # Collect Reddit content
            if 'reddit' in profiles:
                reddit_user = self.reddit.redditor(profiles['reddit'])
                comments = reddit_user.comments.new(limit=50)
                content.extend([comment.body for comment in comments])
            
            # Collect LinkedIn content
            if 'linkedin' in profiles:
                profile = self.linkedin.get_profile(profiles['linkedin'])
                if 'summary' in profile:
                    content.append(profile['summary'])
                
            # Analyze content using OpenAI
            return await self._analyze_with_openai(content)
            
        except Exception as e:
            logger.error(f"Error analyzing social content: {str(e)}")
            return {}
    
    async def _analyze_with_openai(self, content: List[str]) -> Dict:
        """Use OpenAI to analyze content and create psychological profile."""
        try:
            # Combine content with reasonable length limit
            combined_content = " ".join(content)[:8000]  # Limit to 8000 chars
            
            # Create prompt for OpenAI
            prompt = f"""Analyze the following social media content and create a psychological profile. 
            Consider:
            1. Communication style
            2. Interests and values
            3. Decision-making patterns
            4. Emotional tendencies
            5. Professional interests
            
            Content: {combined_content}
            
            Provide analysis in JSON format with these keys:
            - personality_traits
            - communication_preferences
            - interests
            - values
            - decision_style
            - email_recommendations
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a psychological profiling expert."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {str(e)}")
            return {}
    
    def get_content_preferences(self, profile: Dict) -> Dict:
        """Generate content preferences based on psychological profile."""
        preferences = {
            'tone': 'professional',  # Default values
            'style': 'direct',
            'topics': [],
            'personalization_level': 'medium'
        }
        
        try:
            # Adjust tone based on personality traits
            if 'personality_traits' in profile:
                traits = profile['personality_traits']
                if 'informal' in traits.lower() or 'casual' in traits.lower():
                    preferences['tone'] = 'casual'
                elif 'formal' in traits.lower():
                    preferences['tone'] = 'formal'
            
            # Adjust style based on decision style
            if 'decision_style' in profile:
                style = profile['decision_style']
                if 'analytical' in style.lower():
                    preferences['style'] = 'detailed'
                elif 'intuitive' in style.lower():
                    preferences['style'] = 'concise'
            
            # Extract topics of interest
            if 'interests' in profile:
                preferences['topics'] = profile['interests']
            
            # Set personalization level
            if 'communication_preferences' in profile:
                prefs = profile['communication_preferences']
                if 'personal' in prefs.lower():
                    preferences['personalization_level'] = 'high'
                elif 'professional' in prefs.lower():
                    preferences['personalization_level'] = 'low'
            
        except Exception as e:
            logger.error(f"Error generating content preferences: {str(e)}")
        
        return preferences
