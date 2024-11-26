import os
import json
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import requests
from linkedin_api import Linkedin
import praw
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from instabot import Bot as InstaBot
from tiktok_uploader.upload import upload_video
import random
import sqlite3
import re
from performance_db import PerformanceDB
from trend_analyzer import TrendAnalyzer
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip, TextClip, AudioFileClip
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

class VideoContentGenerator:
    """Generates viral-worthy video content for social media"""
    
    def __init__(self):
        self.transitions = {
            'smooth_fade': lambda clip: clip.crossfadein(0.5),
            'slide_left': lambda clip: clip.set_position(lambda t: (1920 * (1-t/1), 0)),
            'zoom_in': lambda clip: clip.resize(lambda t: 1 + 0.3*t)
        }
        
        self.music_categories = {
            'luxury': ['elegant_piano.mp3', 'ambient_luxury.mp3'],
            'modern': ['upbeat_electronic.mp3', 'trendy_pop.mp3'],
            'dramatic': ['cinematic_reveal.mp3', 'emotional_strings.mp3']
        }
        
        self.reel_templates = {
            'before_after': {
                'duration': 30,
                'segments': [
                    {'type': 'text', 'duration': 3, 'content': 'Before'},
                    {'type': 'image', 'duration': 4, 'transition': 'smooth_fade'},
                    {'type': 'text', 'duration': 3, 'content': 'After'},
                    {'type': 'image', 'duration': 4, 'transition': 'zoom_in'},
                    {'type': 'text', 'duration': 3, 'content': 'Transform your space with Design Gaga'}
                ]
            },
            'quick_tips': {
                'duration': 15,
                'segments': [
                    {'type': 'text', 'duration': 2, 'content': '3 Luxury Staging Tips'},
                    {'type': 'tip', 'duration': 3},
                    {'type': 'tip', 'duration': 3},
                    {'type': 'tip', 'duration': 3},
                    {'type': 'outro', 'duration': 4}
                ]
            },
            'property_showcase': {
                'duration': 45,
                'segments': [
                    {'type': 'intro', 'duration': 5},
                    {'type': 'room_sequence', 'duration': 30},
                    {'type': 'highlights', 'duration': 5},
                    {'type': 'outro', 'duration': 5}
                ]
            }
        }

    def create_viral_reel(self, template: str, assets: Dict, style: str = 'luxury') -> str:
        """Create a viral-worthy reel using provided template and assets"""
        try:
            template_config = self.reel_templates[template]
            clips = []
            
            for segment in template_config['segments']:
                if segment['type'] == 'text':
                    clip = self._create_text_clip(
                        segment['content'],
                        duration=segment['duration'],
                        style=style
                    )
                elif segment['type'] == 'image':
                    clip = self._create_image_clip(
                        assets['images'][len(clips) % len(assets['images'])],
                        duration=segment['duration']
                    )
                    if 'transition' in segment:
                        clip = self.transitions[segment['transition']](clip)
                elif segment['type'] == 'tip':
                    clip = self._create_tip_clip(
                        assets['tips'][len(clips) % len(assets['tips'])],
                        duration=segment['duration']
                    )
                elif segment['type'] == 'room_sequence':
                    clip = self._create_room_sequence(
                        assets['room_images'],
                        duration=segment['duration']
                    )
                
                clips.append(clip)
            
            # Combine clips
            final_video = concatenate_videoclips(clips)
            
            # Add music
            music = self._add_background_music(style, template_config['duration'])
            final_video = CompositeVideoClip([final_video.set_audio(music)])
            
            # Add branding
            final_video = self._add_branding(final_video)
            
            # Export
            output_path = f"content/reels/{template}_{int(time.time())}.mp4"
            final_video.write_videofile(output_path, fps=30)
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error creating viral reel: {str(e)}")
            return None

    def _create_text_clip(self, text: str, duration: int, style: str) -> TextClip:
        """Create stylized text clip"""
        font_settings = {
            'luxury': ('Didot', 80, 'white'),
            'modern': ('Helvetica', 70, 'white'),
            'dramatic': ('Trajan Pro', 90, 'gold')
        }
        
        font, size, color = font_settings.get(style, font_settings['luxury'])
        
        text_clip = TextClip(
            text,
            fontsize=size,
            font=font,
            color=color,
            bg_color='transparent',
            kerning=2,
            interline=-1
        ).set_duration(duration)
        
        # Add animation
        text_clip = text_clip.set_position('center').crossfadein(0.5)
        
        return text_clip

    def _create_image_clip(self, image_path: str, duration: int) -> ImageClip:
        """Create enhanced image clip with cinematic effects"""
        # Load and enhance image
        img = Image.open(image_path)
        
        # Apply luxury enhancements
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        
        # Add subtle blur for depth
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Convert to clip
        clip = ImageClip(np.array(img)).set_duration(duration)
        
        # Add Ken Burns effect
        clip = clip.resize(lambda t: 1 + 0.1*t)
        
        return clip

    def _create_room_sequence(self, images: List[str], duration: int) -> CompositeVideoClip:
        """Create cinematic room sequence with smooth transitions"""
        clips = []
        per_room_duration = duration / len(images)
        
        for img_path in images:
            clip = self._create_image_clip(img_path, per_room_duration)
            clips.append(clip)
        
        sequence = concatenate_videoclips(clips, method='compose')
        return sequence

    def _add_background_music(self, style: str, duration: int) -> AudioFileClip:
        """Add appropriate background music based on style"""
        music_path = random.choice(self.music_categories[style])
        audio = AudioFileClip(music_path)
        
        # Loop if necessary
        if audio.duration < duration:
            audio = audio.loop(duration=duration)
        else:
            audio = audio.subclip(0, duration)
        
        # Fade in/out
        audio = audio.audio_fadein(1).audio_fadeout(1)
        
        return audio

    def _add_branding(self, video: CompositeVideoClip) -> CompositeVideoClip:
        """Add consistent branding elements"""
        # Add logo
        logo = ImageClip('assets/logo.png')\
            .set_duration(video.duration)\
            .resize(height=80)\
            .set_position((50, 50))\
            .set_opacity(0.8)
        
        # Add website
        website = TextClip(
            'designgaga.ca',
            fontsize=40,
            font='Helvetica',
            color='white'
        ).set_duration(video.duration)\
         .set_position((50, video.h - 80))
        
        return CompositeVideoClip([video, logo, website])

class SocialMediaManager:
    """Manages multiple social media platforms for luxury real estate marketing"""
    
    def __init__(self, credentials_path: str = None):
        """Initialize social media manager"""
        self.setup_logging()
        if credentials_path is None:
            credentials_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
        self.credentials = self._load_credentials(credentials_path)
        self.performance_db = PerformanceDB()
        self.trend_analyzer = TrendAnalyzer(self.credentials)
        self.website_style = self.trend_analyzer.analyze_website_style('https://designgaga.ca')
        self.setup_platforms()
        self.running = False
        self.min_karma_required = 100  # Adjustable based on subreddit requirements
        self.post_cooldown = 3600  # 1 hour between posts, adjustable based on performance
        self.video_generator = VideoContentGenerator()
        
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('social_media.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('SocialMediaManager')
        
    def _load_credentials(self, credentials_path: str) -> Dict:
        """Load social media credentials from file"""
        try:
            with open(credentials_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            return {}
            
    def setup_platforms(self):
        """Initialize connections to all social media platforms"""
        self.platforms = {}
        
        # LinkedIn
        try:
            if all(k in self.credentials.get('LINKEDIN', {}) for k in ['username', 'password']):
                self.platforms['linkedin'] = Linkedin(
                    self.credentials['LINKEDIN']['username'],
                    self.credentials['LINKEDIN']['password']
                )
                self.logger.info("Successfully initialized LinkedIn")
        except Exception as e:
            self.logger.error(f"Error initializing LinkedIn: {str(e)}")
            
        # Reddit
        try:
            reddit_creds = self.credentials.get('REDDIT', {})
            if all(k in reddit_creds for k in ['client_id', 'client_secret', 'username', 'password']):
                self.platforms['reddit'] = praw.Reddit(
                    client_id=reddit_creds['client_id'],
                    client_secret=reddit_creds['client_secret'],
                    username=reddit_creds['username'],
                    password=reddit_creds['password'],
                    user_agent="Design Gaga Luxury Real Estate Bot v1.0"
                )
                # Verify credentials
                username = self.platforms['reddit'].user.me()
                if username:
                    self.logger.info(f"Successfully initialized Reddit as {username}")
                else:
                    del self.platforms['reddit']
                    self.logger.error("Reddit authentication failed")
        except Exception as e:
            self.logger.error(f"Error initializing Reddit: {str(e)}")
            
        # Facebook
        try:
            fb_creds = self.credentials.get('FACEBOOK', {})
            if all(k in fb_creds for k in ['app_id', 'app_secret', 'access_token', 'page_id']):
                self.logger.info("Initializing Facebook with credentials...")
                FacebookAdsApi.init(
                    fb_creds['app_id'],
                    fb_creds['app_secret'],
                    fb_creds['access_token']
                )
                self.logger.info("Facebook API initialized, getting page...")
                page = Page(fb_creds['page_id'])
                self.logger.info("Validating page access...")
                # Test the page access
                page.api_get(fields=['name'])
                self.platforms['facebook'] = page
                self.logger.info("Successfully initialized Facebook")
            else:
                missing = [k for k in ['app_id', 'app_secret', 'access_token', 'page_id'] if k not in fb_creds]
                self.logger.error(f"Missing Facebook credentials: {missing}")
        except Exception as e:
            self.logger.error(f"Error initializing Facebook: {str(e)}")
            if hasattr(e, 'api_error_message'):
                self.logger.error(f"Facebook API Error: {e.api_error_message}")
            
        # Instagram
        try:
            insta_creds = self.credentials.get('INSTAGRAM', {})
            if all(k in insta_creds for k in ['username', 'password']):
                insta = InstaBot()
                if insta.login(
                    username=insta_creds['username'],
                    password=insta_creds['password']
                ):
                    self.platforms['instagram'] = insta
                    self.logger.info("Successfully initialized Instagram")
        except Exception as e:
            self.logger.error(f"Error initializing Instagram: {str(e)}")
            
        # TikTok
        try:
            tiktok_creds = self.credentials.get('TIKTOK', {})
            if all(k in tiktok_creds for k in ['username', 'password']):
                self.platforms['tiktok'] = tiktok_creds
                self.logger.info("Successfully initialized TikTok")
        except Exception as e:
            self.logger.error(f"Error initializing TikTok: {str(e)}")
            
        active_platforms = list(self.platforms.keys())
        if active_platforms:
            self.logger.info(f"Successfully initialized platforms: {', '.join(active_platforms)}")
        else:
            self.logger.warning("No social media platforms were successfully initialized")
            
    def create_viral_content(self, content_type: str = 'before_after'):
        """Create viral social media content"""
        try:
            # Prepare assets
            assets = {
                'images': self._get_recent_staging_images(),
                'tips': [
                    "Perfect lighting is key to luxury staging",
                    "Create focal points in each room",
                    "Layer textures for depth and luxury",
                    "Use strategic mirrors to amplify space",
                    "Incorporate high-end accent pieces"
                ],
                'room_images': self._get_room_sequence_images()
            }
            
            # Generate video content
            video_path = self.video_generator.create_viral_reel(
                template=content_type,
                assets=assets,
                style='luxury'
            )
            
            if video_path:
                # Post to multiple platforms
                self._post_video_content(video_path, content_type)
                
                return {
                    'status': 'success',
                    'video_path': video_path,
                    'platforms_posted': ['instagram', 'tiktok', 'facebook']
                }
            
        except Exception as e:
            self.logger.error(f"Error creating viral content: {str(e)}")
            return None

    def _get_recent_staging_images(self) -> List[str]:
        """Get recent high-quality staging images"""
        try:
            # Get images from staging database
            image_paths = []
            # ... implementation to get recent staging images
            return image_paths
        except Exception as e:
            self.logger.error(f"Error getting staging images: {str(e)}")
            return []

    def _get_room_sequence_images(self) -> List[str]:
        """Get sequence of room images for property showcase"""
        try:
            # Get room sequence from recent projects
            room_paths = []
            # ... implementation to get room sequence
            return room_paths
        except Exception as e:
            self.logger.error(f"Error getting room sequence: {str(e)}")
            return []

    def _post_video_content(self, video_path: str, content_type: str):
        """Post video content to multiple platforms"""
        try:
            # Post to Instagram Reels
            if 'instagram' in self.platforms:
                self.platforms['instagram'].post_reel(
                    video_path,
                    caption=self._generate_video_caption(content_type)
                )
            
            # Post to TikTok
            if 'tiktok' in self.platforms:
                self.platforms['tiktok'].post_video(
                    video_path,
                    description=self._generate_video_caption(content_type, platform='tiktok')
                )
            
            # Post to Facebook
            if 'facebook' in self.platforms:
                self.platforms['facebook'].post_video(
                    video_path,
                    description=self._generate_video_caption(content_type, platform='facebook')
                )
            
        except Exception as e:
            self.logger.error(f"Error posting video content: {str(e)}")

    def _generate_video_caption(self, content_type: str, platform: str = 'instagram') -> str:
        """Generate platform-specific video captions"""
        captions = {
            'before_after': {
                'instagram': "✨ Watch the magic unfold! Swipe to see this stunning transformation by Design Gaga.\n\n"
                            "🏠 Professional home staging\n"
                            "🎨 Expert design consultation\n"
                            "📸 Virtual tours\n\n"
                            "Ready to transform your space? Link in bio!\n\n"
                            "#luxurystaging #torontorealestate #interiordesign",
                'tiktok': "✨ Luxury home staging transformation! #luxuryhomes #staging #realestate",
                'facebook': "Experience the power of professional home staging! Watch this incredible transformation..."
            },
            'quick_tips': {
                'instagram': "🏠 3 Pro Tips for Luxury Home Staging\n\n"
                            "Save this post for your next staging project! ✨\n\n"
                            "#homestaging #designtips #luxuryrealestate",
                'tiktok': "🏠 Luxury Staging Secrets Revealed! #staging #luxuryhomes #realestate",
                'facebook': "Want to stage your home like a pro? Here are our top 3 luxury staging tips..."
            }
        }
        
        return captions.get(content_type, {}).get(platform, captions['before_after']['instagram'])

    # ... rest of the code remains the same ...
