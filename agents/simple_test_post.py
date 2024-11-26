import praw
import json

def test_single_response():
    # Load credentials
    with open("../credentials.json", 'r') as f:
        creds = json.load(f)['REDDIT']
    
    # Initialize Reddit instance
    reddit = praw.Reddit(
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        user_agent=creds['user_agent'],
        username=creds['username']
    )
    
    # Get a recent post from r/RealEstate
    subreddit = reddit.subreddit("RealEstate")
    
    print("Looking for relevant posts...")
    
    # Find a suitable post about home staging or selling
    for post in subreddit.new(limit=10):
        if any(keyword in post.title.lower() for keyword in ['stage', 'staging', 'sell', 'selling', 'market']):
            print(f"\nFound relevant post: {post.title}")
            print(f"Post URL: https://reddit.com{post.permalink}")
            
            # Show the post for review
            print("\nWould reply with:")
            print("-------------------")
            print("Hey there! Based on my experience in home staging, "
                  "focusing on decluttering and creating a neutral palette can make a huge difference. "
                  "I've found that professional staging can reduce time on market by 30-50%. "
                  "Check out some examples at designgaga.ca/tips/staging if you're interested. "
                  "Let me know if you need any specific advice!")
            print("-------------------")
            
            return post.url
            
    print("No relevant posts found in the first 10 posts.")
    return None

if __name__ == "__main__":
    post_url = test_single_response()
    if post_url:
        print(f"\nYou can view the post at: {post_url}")
        print("You can now manually post the comment if it looks good!")
