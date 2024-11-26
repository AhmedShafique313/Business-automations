import requests
import json
from typing import List, Dict
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import tweepy
import instaloader
from collections import Counter

class TrendAnalyzer:
    """Analyzes trending topics and hashtags across platforms"""
    
    def __init__(self, credentials: Dict):
        self.setup_logging()
        self.credentials = credentials
        self.instagram = instaloader.Instaloader()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trend_analyzer.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('TrendAnalyzer')
    
    def get_trending_hashtags(self, location: str = "Toronto") -> List[str]:
        """Get trending hashtags from multiple sources"""
        hashtags = []
        
        # Instagram trending hashtags
        hashtags.extend(self._get_instagram_trends(location))
        
        # Real estate specific hashtags
        hashtags.extend([
            '#luxuryrealestate', '#torontorealestate', '#gtarealestate',
            '#luxuryhomes', '#milliondollarlisting', '#dreamhome',
            '#luxurylifestyle', '#realestateagent', '#realestateinvesting'
        ])
        
        # Location specific hashtags
        hashtags.extend([
            f'#{location.replace(" ", "")}realestate',
            f'#{location.replace(" ", "")}homes',
            f'#{location.replace(" ", "")}luxury'
        ])
        
        return list(set(hashtags))  # Remove duplicates
    
    def _get_instagram_trends(self, location: str) -> List[str]:
        """Get trending hashtags from Instagram"""
        try:
            hashtags = []
            search_tags = [
                f'{location.lower()}realestate',
                'luxuryhomes',
                'homestaging'
            ]
            
            for tag in search_tags:
                posts = self.instagram.get_hashtag_posts(tag)
                post_hashtags = []
                
                # Get hashtags from recent posts
                for post in list(posts)[:20]:  # Look at 20 recent posts
                    if hasattr(post, 'caption') and post.caption:
                        tags = [tag.strip('#') for tag in post.caption.split() 
                               if tag.startswith('#')]
                        post_hashtags.extend(tags)
                
                # Get most common hashtags
                common_tags = Counter(post_hashtags).most_common(10)
                hashtags.extend([f'#{tag[0]}' for tag in common_tags])
            
            return list(set(hashtags))
            
        except Exception as e:
            self.logger.error(f"Error getting Instagram trends: {str(e)}")
            return []
    
    def analyze_website_style(self, url: str) -> Dict:
        """Analyze website's tone and style"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            text_content = ' '.join([p.text for p in soup.find_all('p')])
            
            # Analyze tone
            tone_indicators = {
                'professional': len([w for w in text_content.lower().split() 
                                  if w in ['professional', 'expertise', 'experience']]),
                'luxury': len([w for w in text_content.lower().split() 
                             if w in ['luxury', 'exclusive', 'premium']]),
                'friendly': len([w for w in text_content.lower().split() 
                               if w in ['welcome', 'help', 'support']])
            }
            
            # Extract color scheme
            colors = []
            for style in soup.find_all('style'):
                if style.string:
                    colors.extend(re.findall(r'#[0-9a-fA-F]{6}', style.string))
            
            return {
                'tone': max(tone_indicators.items(), key=lambda x: x[1])[0],
                'colors': list(set(colors)),
                'common_phrases': self._extract_common_phrases(text_content)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing website: {str(e)}")
            return {}
    
    def _extract_common_phrases(self, text: str) -> List[str]:
        """Extract commonly used phrases"""
        words = text.lower().split()
        phrases = []
        
        for i in range(len(words)-2):
            phrase = ' '.join(words[i:i+3])
            if any(keyword in phrase for keyword in ['home', 'property', 'estate', 'staging']):
                phrases.append(phrase)
        
        return list(set(phrases))[:10]  # Return top 10 unique phrases
    
    def get_engagement_opportunities(self, hashtags: List[str]) -> List[Dict]:
        """Find posts and accounts to engage with"""
        opportunities = []
        
        try:
            for hashtag in hashtags[:5]:  # Look at top 5 hashtags
                posts = self.instagram.get_hashtag_posts(hashtag.strip('#'))
                
                for post in list(posts)[:10]:  # Look at 10 recent posts per hashtag
                    if hasattr(post, 'owner_profile'):
                        profile = post.owner_profile
                        
                        # Check if this is a relevant account
                        if any(keyword in profile.biography.lower() 
                              for keyword in ['real estate', 'property', 'home']):
                            opportunities.append({
                                'platform': 'instagram',
                                'username': profile.username,
                                'followers': profile.followers,
                                'post_url': f'https://www.instagram.com/p/{post.shortcode}/',
                                'engagement_rate': post.likes / profile.followers if profile.followers > 0 else 0
                            })
            
            # Sort by engagement rate
            opportunities.sort(key=lambda x: x['engagement_rate'], reverse=True)
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error finding engagement opportunities: {str(e)}")
            return []
