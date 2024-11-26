import praw
import json
import asyncio
from datetime import datetime

def load_credentials(path="../credentials.json"):
    with open(path, 'r') as f:
        return json.load(f)['REDDIT']

def test_reddit_connection():
    try:
        # Load credentials
        creds = load_credentials()
        
        # Initialize Reddit client
        reddit = praw.Reddit(
            client_id=creds['client_id'],
            client_secret=creds['client_secret'],
            user_agent=creds['user_agent'],
            username=creds['username']
        )
        
        # Test read access
        print("\nTesting read access to r/RealEstate...")
        subreddit = reddit.subreddit("RealEstate")
        
        print("\nFetching hot posts:")
        for submission in subreddit.hot(limit=3):
            print(f"\nTitle: {submission.title}")
            print(f"Score: {submission.score}")
            print(f"Created: {datetime.fromtimestamp(submission.created_utc)}")
            print(f"URL: {submission.url}")
        
        print("\nConnection test successful!")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_reddit_connection()
