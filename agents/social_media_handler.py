import praw
import json
import os
from typing import Dict, List, Optional
import logging
from linkedin_api import Linkedin
import asyncio
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialMediaHandler:
    def __init__(self, credentials_path: str = "../credentials.json"):
        """Initialize social media handlers with credentials"""
        self.credentials = self._load_credentials(credentials_path)
        self.reddit_client = self._init_reddit()
        self.linkedin_client = self._init_linkedin()
    
    def _load_credentials(self, path: str) -> Dict:
        """Load credentials from JSON file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load credentials: {str(e)}")
            raise
    
    def _init_reddit(self) -> praw.Reddit:
        """Initialize Reddit client with proper error handling"""
        try:
            creds = self.credentials["REDDIT"]
            return praw.Reddit(
                client_id=creds["client_id"],
                client_secret=creds["client_secret"],
                username=creds["username"],
                password=creds["password"],
                user_agent=creds["user_agent"],
                ratelimit_seconds=300  # Be nice to Reddit API
            )
        except KeyError as e:
            logger.error(f"Missing Reddit credential: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {str(e)}")
            raise
    
    def _init_linkedin(self) -> Linkedin:
        """Initialize LinkedIn client with proper error handling"""
        try:
            creds = self.credentials["LINKEDIN"]
            return Linkedin(
                client_id=creds["client_id"],
                client_secret=creds["client_secret"]
            )
        except KeyError as e:
            logger.error(f"Missing LinkedIn credential: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize LinkedIn client: {str(e)}")
            raise
    
    async def post_to_reddit(self, 
                           subreddit: str, 
                           title: str, 
                           content: str,
                           flair: Optional[str] = None) -> Dict:
        """
        Post content to Reddit with rate limiting and error handling
        
        Args:
            subreddit: Subreddit name to post to
            title: Post title
            content: Post content
            flair: Optional flair for the post
        
        Returns:
            Dict containing post details and status
        """
        try:
            # Get subreddit instance
            sub = self.reddit_client.subreddit(subreddit)
            
            # Check if we can post (respecting subreddit rules)
            if not sub.user_is_subscriber:
                logger.warning(f"Not subscribed to r/{subreddit}")
                await asyncio.sleep(2)  # Respect rate limits
                sub.subscribe()
            
            # Submit post
            post = sub.submit(
                title=title,
                selftext=content,
                flair_id=flair if flair else None
            )
            
            logger.info(f"Successfully posted to r/{subreddit}")
            return {
                "success": True,
                "post_id": post.id,
                "url": post.url,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except praw.exceptions.APIException as e:
            logger.error(f"Reddit API error: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Failed to post to Reddit: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def post_to_linkedin(self, 
                             content: str,
                             media_urls: Optional[List[str]] = None) -> Dict:
        """
        Post content to LinkedIn with proper error handling
        
        Args:
            content: Post content
            media_urls: Optional list of media URLs to attach
        
        Returns:
            Dict containing post details and status
        """
        try:
            # Create post
            post = self.linkedin_client.post(
                text=content,
                media_urls=media_urls if media_urls else None
            )
            
            logger.info("Successfully posted to LinkedIn")
            return {
                "success": True,
                "post_id": post["id"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to post to LinkedIn: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def analyze_reddit_engagement(self, post_id: str) -> Dict:
        """Analyze Reddit post engagement"""
        try:
            post = self.reddit_client.submission(id=post_id)
            return {
                "upvotes": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "is_locked": post.locked,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to analyze Reddit engagement: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def analyze_linkedin_engagement(self, post_id: str) -> Dict:
        """Analyze LinkedIn post engagement"""
        try:
            post = self.linkedin_client.get_post(post_id)
            return {
                "likes": post.get("numLikes", 0),
                "comments": post.get("numComments", 0),
                "shares": post.get("numShares", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to analyze LinkedIn engagement: {str(e)}")
            return {"success": False, "error": str(e)}


# Example usage
if __name__ == "__main__":
    # Initialize handler
    handler = SocialMediaHandler()
    
    # Example content
    title = "Exciting Real Estate Opportunity in San Francisco!"
    content = """
    🏠 Just listed: Stunning property in the heart of San Francisco!
    
    Key Features:
    - 3 bedrooms, 2 bathrooms
    - Modern kitchen with high-end appliances
    - Walking distance to tech hubs
    - Incredible city views
    
    DM for more details or schedule a viewing!
    #SFRealEstate #Investment #LuxuryHomes
    """
    
    # Post to both platforms
    async def main():
        # Post to Reddit
        reddit_result = await handler.post_to_reddit(
            subreddit="RealEstate",
            title=title,
            content=content
        )
        print("Reddit Result:", reddit_result)
        
        # Post to LinkedIn
        linkedin_result = await handler.post_to_linkedin(content=content)
        print("LinkedIn Result:", linkedin_result)
        
        # Analyze engagement after a delay
        if reddit_result.get("success"):
            await asyncio.sleep(3600)  # Wait 1 hour
            reddit_engagement = await handler.analyze_reddit_engagement(
                reddit_result["post_id"]
            )
            print("Reddit Engagement:", reddit_engagement)
    
    # Run the example
    asyncio.run(main())
