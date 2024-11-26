import praw
import json
import random

def test_single_response():
    # Load credentials
    with open("../credentials.json", 'r') as f:
        creds = json.load(f)['REDDIT']
    
    # Initialize Reddit instance with your main account
    reddit = praw.Reddit(
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        user_agent=creds['user_agent'],
        username=creds['username'],
        password=creds['password']
    )
    
    # Get a recent post from r/RealEstate
    subreddit = reddit.subreddit("RealEstate")
    
    # Find a suitable post about home staging or selling
    for post in subreddit.new(limit=10):
        if any(keyword in post.title.lower() for keyword in ['stage', 'staging', 'sell', 'selling', 'market']):
            print(f"\nFound relevant post: {post.title}")
            print(f"Post URL: https://reddit.com{post.permalink}")
            
            # Generate a natural, helpful response
            response = (
                "Hey there! Based on my experience in home staging, "
                "focusing on decluttering and creating a neutral palette can make a huge difference. "
                "I've found that professional staging can reduce time on market by 30-50%. "
                "Check out some examples at designgaga.ca/tips/staging if you're interested. "
                "Let me know if you need any specific advice!"
            )
            
            # Post the comment
            comment = post.reply(response)
            print(f"\nPosted comment: {response}")
            print(f"Comment URL: https://reddit.com{comment.permalink}")
            break

if __name__ == "__main__":
    test_single_response()
