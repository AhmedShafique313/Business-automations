"""
Channel Manager
Handles content distribution across different channels.
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path
import json
import asyncio
from datetime import datetime

# Channel-specific imports
from linkedin import Linkedin
from facebook_business import FacebookAdsApi
from twitter import Api as TwitterApi
from instabot import Bot as InstagramBot
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class ChannelManager:
    """Manages content distribution across different channels."""
    
    def __init__(self, config: Dict):
        """Initialize channel manager."""
        self.logger = logging.getLogger('ChannelManager')
        self.config = config
        self.channels = {}
        self._initialize_channels()
    
    def _initialize_channels(self):
        """Initialize channel connections."""
        try:
            # Initialize LinkedIn
            if 'linkedin' in self.config:
                self.channels['linkedin'] = Linkedin(
                    self.config['linkedin']['access_token']
                )
            
            # Initialize Facebook
            if 'facebook' in self.config:
                FacebookAdsApi.init(
                    access_token=self.config['facebook']['access_token']
                )
                self.channels['facebook'] = FacebookAdsApi.get_default_api()
            
            # Initialize Twitter
            if 'twitter' in self.config:
                self.channels['twitter'] = TwitterApi(
                    consumer_key=self.config['twitter']['consumer_key'],
                    consumer_secret=self.config['twitter']['consumer_secret'],
                    access_token_key=self.config['twitter']['access_token'],
                    access_token_secret=self.config['twitter']['access_token_secret']
                )
            
            # Initialize Instagram
            if 'instagram' in self.config:
                bot = InstagramBot()
                bot.login(
                    username=self.config['instagram']['username'],
                    password=self.config['instagram']['password']
                )
                self.channels['instagram'] = bot
            
            # Initialize Email (SendGrid)
            if 'sendgrid' in self.config:
                self.channels['email'] = SendGridAPIClient(
                    self.config['sendgrid']['api_key']
                )
            
            self.logger.info("Channel connections initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize channels: {str(e)}")
            raise
    
    async def distribute_content(self, content: Dict, channel: str) -> Dict:
        """Distribute content to a specific channel."""
        try:
            if channel not in self.channels:
                raise ValueError(f"Channel not configured: {channel}")
            
            # Get channel-specific distributor
            distributor = getattr(self, f"_distribute_to_{channel}")
            if not distributor:
                raise ValueError(f"Distribution not implemented for channel: {channel}")
            
            # Distribute content
            result = await distributor(content)
            
            return {
                'channel': channel,
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'result': result
            }
            
        except Exception as e:
            self.logger.error(f"Failed to distribute to {channel}: {str(e)}")
            return {
                'channel': channel,
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def _distribute_to_linkedin(self, content: Dict) -> Dict:
        """Distribute content to LinkedIn."""
        try:
            # Prepare content
            post = {
                'author': 'urn:li:person:' + self.config['linkedin']['user_id'],
                'lifecycleState': 'PUBLISHED',
                'specificContent': {
                    'com.linkedin.ugc.ShareContent': {
                        'shareCommentary': {
                            'text': content['content']
                        },
                        'shareMediaCategory': 'NONE'
                    }
                },
                'visibility': {
                    'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
                }
            }
            
            # Add media if present
            if content.get('media'):
                media_assets = []
                for media in content['media']:
                    asset = self.channels['linkedin'].upload_media(
                        media['url'],
                        media['type']
                    )
                    media_assets.append(asset)
                
                post['specificContent']['com.linkedin.ugc.ShareContent']['shareMediaCategory'] = 'IMAGE'
                post['specificContent']['com.linkedin.ugc.ShareContent']['media'] = media_assets
            
            # Post content
            response = self.channels['linkedin'].make_post(post)
            
            return {
                'post_id': response['id'],
                'url': f"https://www.linkedin.com/feed/update/{response['id']}"
            }
            
        except Exception as e:
            self.logger.error(f"LinkedIn distribution failed: {str(e)}")
            raise
    
    async def _distribute_to_twitter(self, content: Dict) -> Dict:
        """Distribute content to Twitter."""
        try:
            tweet_text = content['content']
            media_ids = []
            
            # Upload media if present
            if content.get('media'):
                for media in content['media']:
                    media_id = self.channels['twitter'].UploadMediaChunked(
                        media_file=media['url']
                    )
                    media_ids.append(media_id)
            
            # Post tweet
            status = self.channels['twitter'].PostUpdate(
                tweet_text,
                media=media_ids if media_ids else None
            )
            
            return {
                'tweet_id': status.id,
                'url': f"https://twitter.com/i/web/status/{status.id}"
            }
            
        except Exception as e:
            self.logger.error(f"Twitter distribution failed: {str(e)}")
            raise
    
    async def _distribute_to_facebook(self, content: Dict) -> Dict:
        """Distribute content to Facebook."""
        try:
            page_id = self.config['facebook']['page_id']
            
            # Prepare post data
            post_data = {
                'message': content['content']
            }
            
            # Add media if present
            if content.get('media'):
                media_ids = []
                for media in content['media']:
                    media_response = self.channels['facebook'].post(
                        f"{page_id}/photos",
                        params={
                            'url': media['url'],
                            'published': False
                        }
                    )
                    media_ids.append(media_response['id'])
                
                post_data['attached_media'] = [
                    {'media_fbid': media_id} for media_id in media_ids
                ]
            
            # Create post
            response = self.channels['facebook'].post(
                f"{page_id}/feed",
                params=post_data
            )
            
            return {
                'post_id': response['id'],
                'url': f"https://facebook.com/{response['id']}"
            }
            
        except Exception as e:
            self.logger.error(f"Facebook distribution failed: {str(e)}")
            raise
    
    async def _distribute_to_instagram(self, content: Dict) -> Dict:
        """Distribute content to Instagram."""
        try:
            caption = content['content']
            
            # Instagram requires at least one image
            if not content.get('media'):
                raise ValueError("Instagram posts require at least one image")
            
            # Upload media
            media_urls = [media['url'] for media in content['media']]
            
            if len(media_urls) == 1:
                # Single photo post
                response = self.channels['instagram'].upload_photo(
                    media_urls[0],
                    caption=caption
                )
            else:
                # Multiple photo post
                response = self.channels['instagram'].upload_album(
                    media_urls,
                    caption=caption
                )
            
            return {
                'media_id': response['media_id'],
                'url': f"https://instagram.com/p/{response['code']}"
            }
            
        except Exception as e:
            self.logger.error(f"Instagram distribution failed: {str(e)}")
            raise
    
    async def _distribute_to_email(self, content: Dict) -> Dict:
        """Distribute content via email."""
        try:
            # Create email message
            message = Mail(
                from_email=self.config['sendgrid']['from_email'],
                to_emails=content['recipients'],
                subject=content['subject'],
                html_content=content['content']
            )
            
            # Send email
            response = self.channels['email'].send(message)
            
            return {
                'message_id': response.headers['X-Message-Id'],
                'status_code': response.status_code
            }
            
        except Exception as e:
            self.logger.error(f"Email distribution failed: {str(e)}")
            raise
    
    async def distribute_to_multiple(self, content: Dict, channels: List[str]) -> List[Dict]:
        """Distribute content to multiple channels."""
        try:
            tasks = []
            for channel in channels:
                task = asyncio.create_task(
                    self.distribute_content(content, channel)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return [
                result if not isinstance(result, Exception)
                else {
                    'channel': channels[i],
                    'status': 'error',
                    'error': str(result),
                    'timestamp': datetime.now().isoformat()
                }
                for i, result in enumerate(results)
            ]
            
        except Exception as e:
            self.logger.error(f"Multi-channel distribution failed: {str(e)}")
            raise
    
    def validate_channel_config(self, channel: str) -> bool:
        """Validate channel configuration."""
        try:
            if channel not in self.config:
                return False
            
            required_fields = {
                'linkedin': ['access_token', 'user_id'],
                'twitter': ['consumer_key', 'consumer_secret', 'access_token', 'access_token_secret'],
                'facebook': ['access_token', 'page_id'],
                'instagram': ['username', 'password'],
                'email': ['api_key', 'from_email']
            }
            
            return all(
                field in self.config[channel]
                for field in required_fields.get(channel, [])
            )
            
        except Exception as e:
            self.logger.error(f"Config validation failed: {str(e)}")
            return False
