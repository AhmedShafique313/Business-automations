import asyncpraw
import json
import asyncio

async def test_reddit_read_only():
    try:
        # Load credentials
        with open("../credentials.json", 'r') as f:
            creds = json.load(f)
        reddit_creds = creds["REDDIT"]
        
        # Initialize Reddit client in read-only mode
        reddit = asyncpraw.Reddit(
            client_id=reddit_creds["client_id"],
            client_secret=reddit_creds["client_secret"],
            user_agent=reddit_creds["user_agent"]
        )
        
        # Test read access
        print("Testing read access...")
        subreddit = await reddit.subreddit("RealEstate")
        
        # Get hot posts
        print("\nFetching hot posts from r/RealEstate:")
        async for submission in subreddit.hot(limit=3):
            print(f"\nTitle: {submission.title}")
            print(f"Score: {submission.score}")
            print(f"URL: {submission.url}")
        
        print("\nRead-only test successful!")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        await reddit.close()

if __name__ == "__main__":
    asyncio.run(test_reddit_read_only())
