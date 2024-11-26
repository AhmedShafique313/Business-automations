import praw
import json
import time
import random
from datetime import datetime, timedelta
from pylucene import *
import threading
import numpy as np

# Initialize Lucene
initVM()

class SmartRedditBot:
    def __init__(self, credentials_path="../credentials.json"):
        # Load credentials
        with open(credentials_path, 'r') as f:
            self.creds = json.load(f)['REDDIT']
        
        # Initialize Reddit
        self.reddit = praw.Reddit(
            client_id=self.creds['client_id'],
            client_secret=self.creds['client_secret'],
            user_agent=self.creds['user_agent'],
            username=self.creds['username']
        )
        
        # Casual responses that sound human
        self.intros = [
            "Hey there! ",
            "Just saw your post. ",
            "Interesting question. ",
            "I can help with this. ",
            "Great topic! "
        ]
        
        self.transitions = [
            "From what I've seen, ",
            "In my experience, ",
            "Usually, ",
            "I'd say ",
            "Generally, "
        ]
        
        self.closings = [
            "Hope this helps!",
            "Let me know if you need more info.",
            "Feel free to ask any questions.",
            "Good luck!",
            "Hope that's useful."
        ]
        
        # Randomize posting frequency - adjusted to Reddit's rate limits
        self.min_delay = 3600  # 1 hour
        self.max_delay = 14400  # 4 hours
        
        # Track our interactions
        self.recent_posts = set()
        self.daily_comments = 0
        self.last_reset = datetime.now()
        self.weekly_comments = 0
        self.last_weekly_reset = datetime.now()

    def create_natural_response(self, topic):
        """Create a human-like response with natural variation"""
        intro = random.choice(self.intros)
        transition = random.choice(self.transitions)
        closing = random.choice(self.closings)
        
        # Topic-specific advice
        if "staging" in topic.lower():
            advice = "decluttering makes a huge difference. I've found that neutral colors work best."
        elif "selling" in topic.lower():
            advice = "pricing it right from the start is key. The first two weeks are crucial."
        else:
            advice = "small updates to lighting and paint can really transform a space."
            
        # Randomly include website reference (70% chance)
        if random.random() < 0.7:
            website = " I wrote about this at designgaga.ca/tips if you're interested."
        else:
            website = ""
            
        return f"{intro}{transition}{advice}{website} {closing}"

    def should_engage(self, post):
        """Smart decision making for engagement"""
        # Avoid repeated interactions
        if post.id in self.recent_posts:
            return False
            
        # Reset daily counter if needed
        if (datetime.now() - self.last_reset).days >= 1:
            self.daily_comments = 0
            self.last_reset = datetime.now()
            
        # Reset weekly counter if needed
        if (datetime.now() - self.last_weekly_reset).days >= 7:
            self.weekly_comments = 0
            self.last_weekly_reset = datetime.now()
            
        # Limit daily comments (max 10 per day)
        if self.daily_comments >= 10:
            return False
            
        # Limit weekly comments (max 50 per week)
        if self.weekly_comments >= 50:
            return False
            
        # Check post age
        post_age = datetime.now() - datetime.fromtimestamp(post.created_utc)
        if post_age > timedelta(hours=24):
            return False
            
        # Don't engage if post has too many comments (avoid high-traffic posts)
        if post.num_comments > 50:
            return False
            
        return True

    def monitor_reddit(self):
        """Monitor Reddit with human-like patterns"""
        subreddits = ["RealEstate", "HomeImprovement", "InteriorDesign"]
        
        while True:
            try:
                # Random subreddit selection
                subreddit = self.reddit.subreddit(random.choice(subreddits))
                
                # Check new posts
                for post in subreddit.new(limit=5):
                    if self.should_engage(post):
                        response = self.create_natural_response(post.title)
                        post.reply(response)
                        
                        # Update tracking
                        self.recent_posts.add(post.id)
                        self.daily_comments += 1
                        self.weekly_comments += 1
                        
                        # Random delay between comments
                        time.sleep(random.uniform(self.min_delay, self.max_delay))
                
            except Exception as e:
                print(f"Oops, hit a snag: {str(e)}")
                time.sleep(300)  # 5 min cooldown on error

if __name__ == "__main__":
    bot = SmartRedditBot()
    bot.monitor_reddit()
