import praw
import json
import asyncio

def load_credentials(path: str = "../credentials.json"):
    with open(path, 'r') as f:
        return json.load(f)

async def test_reddit_connection():
    # Load credentials
    creds = load_credentials()
    reddit_creds = creds["REDDIT"]
    
    # Initialize Reddit client
    reddit = praw.Reddit(
        client_id=reddit_creds["client_id"],
        client_secret=reddit_creds["client_secret"],
        username=reddit_creds["username"],
        password=reddit_creds["password"],
        user_agent=reddit_creds["user_agent"]
    )
    
    try:
        # Test authentication
        print(f"Authenticated as: {reddit.user.me()}")
        
        # Test read access
        print("\nTesting read access...")
        subreddit = reddit.subreddit("RealEstate")
        print(f"Accessing r/{subreddit.display_name}")
        print(f"Title: {subreddit.title}")
        print(f"Description: {subreddit.description[:100]}...")
        
        # Test submission capabilities
        print("\nTesting post creation capabilities...")
        print("Can submit to RealEstate:", subreddit.can_submit())
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_reddit_connection())
