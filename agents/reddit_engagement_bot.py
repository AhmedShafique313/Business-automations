import praw
import json
import time
from datetime import datetime, timedelta
import random
import re

class RedditEngagementBot:
    def __init__(self, credentials_path="../credentials.json"):
        with open(credentials_path, 'r') as f:
            self.creds = json.load(f)['REDDIT']
        
        self.reddit = praw.Reddit(
            client_id=self.creds['client_id'],
            client_secret=self.creds['client_secret'],
            user_agent=self.creds['user_agent'],
            username=self.creds['username']
        )
        
        # Subreddits to monitor
        self.target_subreddits = [
            "RealEstate",
            "FirstTimeHomeBuyer",
            "HomeImprovement",
            "InteriorDesign",
            "HomeStaging",
            "RealEstateCanada"
        ]
        
        # Keywords to look for
        self.keywords = [
            "staging",
            "home staging",
            "sell house",
            "selling home",
            "stage house",
            "interior design",
            "home presentation",
            "curb appeal",
            "property value",
            "home makeover"
        ]
        
    def generate_helpful_response(self, post_title, post_body):
        """Generate a personalized, helpful response based on the post content."""
        # Base response templates
        responses = [
            "Based on my experience in home staging, {advice}. You might find some helpful tips on this topic at designgaga.ca/blog/{topic}",
            "I've worked with similar situations before. {advice}. I've written a detailed guide about this at designgaga.ca/resources/{topic}",
            "Great question! {advice}. For more detailed strategies, check out designgaga.ca/tips/{topic}"
        ]
        
        # Customize advice based on post content
        if "staging" in post_title.lower() or "staging" in post_body.lower():
            advice = "focusing on decluttering and creating a neutral palette can make a huge difference"
            topic = "home-staging-tips"
        elif "sell" in post_title.lower() or "selling" in post_body.lower():
            advice = "proper staging can increase your home's value by 5-10%"
            topic = "maximize-home-value"
        else:
            advice = "professional staging can significantly reduce time on market"
            topic = "quick-sale-tips"
        
        response = random.choice(responses).format(advice=advice, topic=topic)
        return response

    def monitor_subreddits(self):
        """Monitor subreddits for relevant posts and respond helpfully."""
        print(f"Starting to monitor subreddits: {', '.join(self.target_subreddits)}")
        
        while True:
            try:
                # Monitor each subreddit
                for subreddit_name in self.target_subreddits:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Check new posts
                    for post in subreddit.new(limit=10):
                        # Skip if post is older than 24 hours
                        if (datetime.utcnow() - datetime.fromtimestamp(post.created_utc)) > timedelta(hours=24):
                            continue
                        
                        # Check if post contains relevant keywords
                        if any(keyword in post.title.lower() or 
                              (hasattr(post, 'selftext') and keyword in post.selftext.lower()) 
                              for keyword in self.keywords):
                            
                            # Check if we haven't already responded
                            already_replied = any(comment.author == self.reddit.user.me() 
                                               for comment in post.comments.list())
                            
                            if not already_replied:
                                # Generate and post helpful response
                                response = self.generate_helpful_response(
                                    post.title,
                                    post.selftext if hasattr(post, 'selftext') else ""
                                )
                                post.reply(response)
                                print(f"Responded to post: {post.title}")
                                
                                # Wait random time to avoid spam detection
                                time.sleep(random.uniform(180, 300))  # 3-5 minutes
                
                # Wait before next round of monitoring
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                print(f"Error: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    bot = RedditEngagementBot()
    bot.monitor_subreddits()
