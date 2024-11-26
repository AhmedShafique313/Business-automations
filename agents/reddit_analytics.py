import praw
import json
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from praw.exceptions import RedditAPIException

class RedditAnalytics:
    def __init__(self):
        # Load credentials
        with open("../credentials.json", 'r') as f:
            self.creds = json.load(f)['REDDIT']
        
        # Initialize Reddit instance
        self.reddit = praw.Reddit(
            client_id=self.creds['client_id'],
            client_secret=self.creds['client_secret'],
            user_agent=self.creds['user_agent'],
            username=self.creds['username']
        )

    def verify_account(self):
        """Verify account connection and permissions"""
        print("\n🔍 Checking Account Connection...")
        try:
            user = self.reddit.user.me()
            if user:
                print(f"✅ Successfully connected as: {user.name}")
                print(f"Account created: {datetime.fromtimestamp(user.created_utc)}")
                print(f"Karma: {user.link_karma} (post) / {user.comment_karma} (comment)")
            else:
                print("❌ Not authenticated - Please check credentials")
                return False
        except Exception as e:
            print(f"❌ Authentication Error: {str(e)}")
            return False
        
        return True

    def analyze_subreddit_engagement(self):
        """Analyze engagement in target subreddits"""
        print("\n📊 Analyzing Subreddit Engagement...")
        
        subreddits = [
            "RealEstate", "HomeImprovement", "InteriorDesign",
            "RealEstateInvesting", "HomeDecorating"
        ]
        
        engagement_data = []
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get subreddit stats
                posts = list(subreddit.new(limit=100))
                avg_comments = sum(post.num_comments for post in posts) / len(posts)
                avg_score = sum(post.score for post in posts) / len(posts)
                
                # Calculate best posting times
                post_times = [datetime.fromtimestamp(post.created_utc).hour for post in posts]
                most_active_hour = max(set(post_times), key=post_times.count)
                
                engagement_data.append({
                    'subreddit': subreddit_name,
                    'subscribers': subreddit.subscribers,
                    'avg_comments': round(avg_comments, 2),
                    'avg_score': round(avg_score, 2),
                    'best_time': f"{most_active_hour}:00",
                    'active_users': subreddit.active_user_count if hasattr(subreddit, 'active_user_count') else 'N/A'
                })
                
            except Exception as e:
                print(f"Error analyzing r/{subreddit_name}: {str(e)}")
        
        # Convert to DataFrame for better visualization
        df = pd.DataFrame(engagement_data)
        print("\nSubreddit Engagement Analysis:")
        print(df.to_string(index=False))
        
        return df

    def analyze_post_success(self):
        """Analyze what types of posts are most successful"""
        print("\n🎯 Analyzing Post Success Patterns...")
        
        try:
            # Get user's comment history
            user = self.reddit.user.me()
            comments = list(user.comments.new(limit=100))
            
            if not comments:
                print("No comments found - Account has not posted yet")
                return
            
            # Analyze comment performance
            comment_data = []
            for comment in comments:
                comment_data.append({
                    'subreddit': comment.subreddit.display_name,
                    'score': comment.score,
                    'length': len(comment.body),
                    'hour_posted': datetime.fromtimestamp(comment.created_utc).hour,
                    'age': (datetime.now() - datetime.fromtimestamp(comment.created_utc)).days
                })
            
            df = pd.DataFrame(comment_data)
            
            print("\nComment Performance Summary:")
            print(f"Total Comments Analyzed: {len(df)}")
            print(f"Average Score: {df['score'].mean():.2f}")
            print(f"Best Performing Subreddit: {df.groupby('subreddit')['score'].mean().idxmax()}")
            print(f"Best Posting Hour: {df.groupby('hour_posted')['score'].mean().idxmax()}:00")
            
            return df
            
        except Exception as e:
            print(f"Error analyzing post success: {str(e)}")
            return None

    def generate_recommendations(self, engagement_df, success_df=None):
        """Generate actionable recommendations based on analysis"""
        print("\n💡 Recommendations:")
        
        # Sort subreddits by engagement potential
        best_subreddits = engagement_df.sort_values('avg_comments', ascending=False)
        
        print("\n1. Top Subreddits for Engagement:")
        for _, row in best_subreddits.head(3).iterrows():
            print(f"   • r/{row['subreddit']}: {row['avg_comments']} avg comments, best time: {row['best_time']}")
        
        if success_df is not None and not success_df.empty:
            best_hours = success_df.groupby('hour_posted')['score'].mean().sort_values(ascending=False)
            
            print("\n2. Optimal Posting Times:")
            for hour in best_hours.head(3).index:
                print(f"   • {hour}:00 (Avg Score: {best_hours[hour]:.2f})")
            
            print("\n3. Content Recommendations:")
            avg_length = success_df[success_df['score'] > success_df['score'].mean()]['length'].mean()
            print(f"   • Optimal comment length: {avg_length:.0f} characters")

def main():
    analytics = RedditAnalytics()
    
    # First verify account
    if not analytics.verify_account():
        return
    
    # Run analysis
    engagement_df = analytics.analyze_subreddit_engagement()
    success_df = analytics.analyze_post_success()
    
    # Generate recommendations
    analytics.generate_recommendations(engagement_df, success_df)

if __name__ == "__main__":
    main()
