from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from instagram_private_api import Client as InstagramAPI

class InstagramCollector:
    """Collects data from Instagram."""
    
    def __init__(self, api: InstagramAPI):
        """Initialize the collector with Instagram API instance."""
        self.api = api
    
    async def fetch_profile_info(self) -> pd.DataFrame:
        """
        Fetch profile information.
        
        Returns:
            DataFrame containing profile information
        """
        try:
            profile = self.api.user_info()
            
            data = [{
                'followers_count': profile['user']['follower_count'],
                'following_count': profile['user']['following_count'],
                'media_count': profile['user']['media_count'],
                'biography': profile['user']['biography'],
                'external_url': profile['user'].get('external_url', ''),
                'is_business': profile['user']['is_business'],
                'timestamp': datetime.now()
            }]
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error fetching Instagram profile info: {e}")
            return pd.DataFrame()
    
    async def fetch_media_insights(self,
                                user_id: str,
                                count: int = 20) -> pd.DataFrame:
        """
        Fetch insights for recent media posts.
        
        Args:
            user_id: Instagram user ID
            count: Number of recent posts to fetch
            
        Returns:
            DataFrame containing media insights
        """
        try:
            feed = self.api.user_feed(user_id, count=count)
            
            data = []
            for item in feed['items']:
                media_id = item['id']
                insights = self.api.media_insights(media_id)
                
                row_data = {
                    'media_id': media_id,
                    'type': item['media_type'],
                    'caption': item.get('caption', {}).get('text', ''),
                    'like_count': item.get('like_count', 0),
                    'comment_count': item.get('comment_count', 0),
                    'timestamp': pd.to_datetime(item['taken_at'], unit='s')
                }
                
                # Add insights metrics
                if 'engagement' in insights:
                    row_data.update({
                        'impressions': insights['impressions']['value'],
                        'reach': insights['reach']['value'],
                        'engagement': insights['engagement']['value'],
                        'saved': insights.get('saved', {}).get('value', 0)
                    })
                
                data.append(row_data)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error fetching Instagram media insights: {e}")
            return pd.DataFrame()
    
    async def fetch_stories_insights(self,
                                  user_id: str) -> pd.DataFrame:
        """
        Fetch insights for active stories.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            DataFrame containing stories insights
        """
        try:
            stories = self.api.user_story_feed(user_id)
            
            data = []
            for story in stories['reel']['items']:
                story_id = story['id']
                insights = self.api.story_insights(story_id)
                
                row_data = {
                    'story_id': story_id,
                    'type': story['media_type'],
                    'timestamp': pd.to_datetime(story['taken_at'], unit='s')
                }
                
                # Add insights metrics
                row_data.update({
                    'impressions': insights['impressions']['value'],
                    'reach': insights['reach']['value'],
                    'replies': insights.get('replies', {}).get('value', 0),
                    'taps_forward': insights.get('taps_forward', {}).get('value', 0),
                    'taps_back': insights.get('taps_back', {}).get('value', 0),
                    'exits': insights.get('exits', {}).get('value', 0)
                })
                
                data.append(row_data)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error fetching Instagram stories insights: {e}")
            return pd.DataFrame()
    
    async def fetch_audience_insights(self) -> pd.DataFrame:
        """
        Fetch audience insights.
        
        Returns:
            DataFrame containing audience insights
        """
        try:
            insights = self.api.insights_account()
            
            data = [{
                'impressions': insights['impressions']['value'],
                'reach': insights['reach']['value'],
                'profile_views': insights['profile_views']['value'],
                'website_clicks': insights.get('website_clicks', {}).get('value', 0),
                'email_clicks': insights.get('email_clicks', {}).get('value', 0),
                'gender_age': insights.get('gender_age', {}),
                'locations': insights.get('locations', {}),
                'timestamp': datetime.now()
            }]
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error fetching Instagram audience insights: {e}")
            return pd.DataFrame()
    
    async def fetch_hashtag_insights(self,
                                  hashtag: str,
                                  count: int = 50) -> pd.DataFrame:
        """
        Fetch insights for a specific hashtag.
        
        Args:
            hashtag: Hashtag to analyze (without #)
            count: Number of recent posts to analyze
            
        Returns:
            DataFrame containing hashtag insights
        """
        try:
            result = self.api.tag_search(hashtag)
            tag_id = result[0]['id']
            
            feed = self.api.tag_feed(tag_id, count=count)
            
            data = []
            for item in feed['items']:
                row_data = {
                    'media_id': item['id'],
                    'user_id': item['user']['pk'],
                    'username': item['user']['username'],
                    'type': item['media_type'],
                    'caption': item.get('caption', {}).get('text', ''),
                    'like_count': item.get('like_count', 0),
                    'comment_count': item.get('comment_count', 0),
                    'timestamp': pd.to_datetime(item['taken_at'], unit='s')
                }
                data.append(row_data)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error fetching Instagram hashtag insights: {e}")
            return pd.DataFrame()
