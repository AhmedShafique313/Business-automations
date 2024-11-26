import asyncpraw
import json
import asyncio

async def load_credentials(path: str = "../credentials.json"):
    with open(path, 'r') as f:
        return json.load(f)

async def test_reddit_connection():
    try:
        # Load credentials
        creds = await load_credentials()
        reddit_creds = creds["REDDIT"]
        
        # Initialize Reddit client
        reddit = asyncpraw.Reddit(
            client_id=reddit_creds["client_id"],
            client_secret=reddit_creds["client_secret"],
            username=reddit_creds["username"],
            password=reddit_creds["password"],
            user_agent=reddit_creds["user_agent"]
        )
        
        # Test authentication
        user = await reddit.user.me()
        print(f"Authenticated as: {user.name}")
        
        # Test read access
        print("\nTesting read access...")
        subreddit = await reddit.subreddit("RealEstate")
        print(f"Accessing r/{subreddit.display_name}")
        
        # Test simple submission (read-only)
        async for submission in subreddit.hot(limit=1):
            print(f"\nFound post: {submission.title}")
            print(f"Score: {submission.score}")
            print(f"URL: {submission.url}")
        
        print("\nConnection test successful!")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        await reddit.close()

if __name__ == "__main__":
    asyncio.run(test_reddit_connection())
