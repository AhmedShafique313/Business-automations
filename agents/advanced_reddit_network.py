import praw
import json
import time
import random
import threading
import queue
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set
import numpy as np
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PersonalityGenerator:
    """Generates unique personalities for agents"""
    WRITING_STYLES = {
        'casual': {
            'intros': ["Hey!", "Quick tip -", "Just sharing:", "FYI -", "Pro tip:"],
            'transitions': ["I found that", "in my experience,", "usually,", "typically,"],
            'closings': ["Hope this helps!", "Good luck!", "Cheers!", "Let me know if you need more info!"]
        },
        'professional': {
            'intros': ["I noticed your post.", "Regarding your question,", "Here's some insight:", "If I may suggest:"],
            'transitions': ["Based on experience,", "Research shows that", "Generally speaking,", "Consider this:"],
            'closings': ["Best regards,", "Hope this is helpful.", "Feel free to reach out.", "All the best."]
        },
        'expert': {
            'intros': ["As a real estate professional,", "From years in the industry,", "In my professional opinion,"],
            'transitions': ["The data suggests that", "Market trends indicate", "Best practices show"],
            'closings': ["Happy to provide more details.", "Let me know if you need clarification.", "Here to help."]
        }
    }

    @staticmethod
    def generate():
        style = random.choice(list(PersonalityGenerator.WRITING_STYLES.keys()))
        return {
            'style': style,
            'chattiness': random.uniform(0.6, 0.9),
            'formality': random.uniform(0.3, 0.8),
            'helpfulness': random.uniform(0.7, 1.0),
            'expertise_areas': random.sample([
                'staging', 'selling', 'buying', 'investment',
                'renovation', 'design', 'market_analysis'
            ], k=random.randint(2, 4))
        }

class RedditAgent:
    def __init__(self, credentials: Dict, agent_id: int):
        self.agent_id = agent_id
        self.reddit = praw.Reddit(
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret'],
            user_agent=f"DesignGaga_{agent_id}",
            username=f"{credentials['username']}_{agent_id}",
            password=credentials['password']
        )
        
        self.personality = PersonalityGenerator.generate()
        self.stats = {
            'daily_comments': 0,
            'weekly_comments': 0,
            'successful_engagements': 0,
            'last_reset': datetime.now(),
            'last_weekly_reset': datetime.now()
        }
        self.recent_posts: Set[str] = set()
        self.engagement_history = defaultdict(int)

    def get_response(self, topic: str, post_data: Dict) -> str:
        """Generate a personalized response based on agent's personality"""
        style = PersonalityGenerator.WRITING_STYLES[self.personality['style']]
        
        # Build response components
        intro = random.choice(style['intros'])
        transition = random.choice(style['transitions'])
        
        # Generate advice based on expertise
        advice = self._generate_expert_advice(topic, post_data)
        
        # Add website reference based on personality
        if random.random() < self.personality['chattiness']:
            relevant_page = self._get_relevant_page(topic)
            website = f" I've written more about this at designgaga.ca/{relevant_page}"
        else:
            website = ""
            
        closing = random.choice(style['closings'])
        
        return f"{intro} {transition} {advice}{website} {closing}"

    def _generate_expert_advice(self, topic: str, post_data: Dict) -> str:
        """Generate expert advice based on agent's expertise areas"""
        expertise = random.choice(self.personality['expertise_areas'])
        
        advice_templates = {
            'staging': [
                "decluttering and neutral colors can increase offers by 5-10%",
                "professional staging typically reduces market time by 30-50%",
                "focusing on kitchen and master bedroom staging gives the best ROI",
                "virtual staging is becoming increasingly effective for online listings"
            ],
            'selling': [
                "pricing within 5% of market value typically leads to faster sales",
                "the first two weeks on market are absolutely crucial",
                "professional photography can increase engagement by 300%",
                "Thursday listings often get more weekend showings"
            ],
            'design': [
                "updating light fixtures gives the best bang for your buck",
                "neutral paint with one accent wall is trending right now",
                "smart home features can increase appeal to younger buyers",
                "outdoor living spaces are becoming major selling points"
            ]
        }
        
        return random.choice(advice_templates.get(expertise, advice_templates['staging']))

    def _get_relevant_page(self, topic: str) -> str:
        """Get relevant website page based on topic"""
        pages = {
            'staging': 'tips/professional-staging',
            'selling': 'guides/quick-sale',
            'design': 'blog/interior-trends',
            'default': 'resources/real-estate'
        }
        return pages.get(topic.lower(), pages['default'])

class NetworkController:
    def __init__(self, num_agents: int = 200):
        self.num_agents = num_agents
        self.agents: List[RedditAgent] = []
        self.work_queue = queue.Queue()
        self.subreddit_stats = defaultdict(lambda: {'posts': 0, 'comments': 0})
        self.load_agents()

    def load_agents(self):
        """Initialize multiple Reddit agents"""
        try:
            with open("../credentials.json", 'r') as f:
                creds = json.load(f)['REDDIT']
                
            for i in range(self.num_agents):
                agent = RedditAgent(creds, i)
                self.agents.append(agent)
                
            logger.info(f"Initialized {len(self.agents)} agents successfully")
        except Exception as e:
            logger.error(f"Agent initialization failed: {str(e)}")

    def should_engage(self, agent: RedditAgent, post) -> bool:
        """Smart engagement decision making"""
        # Basic checks
        if post.id in agent.recent_posts:
            return False
            
        # Reset counters if needed
        current_time = datetime.now()
        if (current_time - agent.stats['last_reset']).days >= 1:
            agent.stats['daily_comments'] = 0
            agent.stats['last_reset'] = current_time
            
        if (current_time - agent.stats['last_weekly_reset']).days >= 7:
            agent.stats['weekly_comments'] = 0
            agent.stats['last_weekly_reset'] = current_time
        
        # Check limits
        if agent.stats['daily_comments'] >= 12:  # Increased limit
            return False
        if agent.stats['weekly_comments'] >= 60:  # Increased limit
            return False
            
        # Advanced checks
        post_age = current_time - datetime.fromtimestamp(post.created_utc)
        if post_age > timedelta(hours=36):  # Increased window
            return False
        
        # Engagement quality checks
        if post.num_comments > 100:  # Increased threshold
            return False
            
        # Personality-based decision
        return random.random() < agent.personality['chattiness']

    def agent_worker(self, agent: RedditAgent):
        """Worker function for each agent thread"""
        while True:
            try:
                subreddit = self.work_queue.get()
                if subreddit is None:
                    break
                
                for post in subreddit.new(limit=5):  # Increased post limit
                    if self.should_engage(agent, post):
                        post_data = {
                            'title': post.title,
                            'body': post.selftext if hasattr(post, 'selftext') else "",
                            'score': post.score,
                            'num_comments': post.num_comments
                        }
                        
                        response = agent.get_response(
                            self._analyze_topic(post_data),
                            post_data
                        )
                        
                        post.reply(response)
                        
                        # Update stats
                        agent.recent_posts.add(post.id)
                        agent.stats['daily_comments'] += 1
                        agent.stats['weekly_comments'] += 1
                        agent.stats['successful_engagements'] += 1
                        
                        # Variable delay (1-4 hours)
                        time.sleep(random.uniform(3600, 14400))
                        
            except Exception as e:
                logger.error(f"Agent {agent.agent_id} error: {str(e)}")
                time.sleep(300)
            finally:
                self.work_queue.task_done()

    def _analyze_topic(self, post_data: Dict) -> str:
        """Analyze post to determine main topic"""
        title_lower = post_data['title'].lower()
        body_lower = post_data['body'].lower()
        
        topics = {
            'staging': ['stage', 'staging', 'presentation', 'prepare'],
            'selling': ['sell', 'selling', 'market', 'list'],
            'design': ['design', 'decor', 'style', 'look']
        }
        
        for topic, keywords in topics.items():
            if any(word in title_lower or word in body_lower for word in keywords):
                return topic
        return 'general'

    def run(self):
        """Start the network"""
        subreddits = [
            "RealEstate", "HomeImprovement", "InteriorDesign",
            "RealEstateInvesting", "HomeDecorating", "RealEstateCanada",
            "HomeStaging", "RealEstatePhotography", "RealEstateAdvice",
            "FirstTimeHomeBuyer", "HouseFlipping", "RealEstateMarketing"
        ]
        
        # Start agent threads
        threads = []
        for agent in self.agents:
            t = threading.Thread(target=self.agent_worker, args=(agent,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Main monitoring loop
        while True:
            try:
                # Randomly select subreddit
                subreddit = random.choice(subreddits)
                self.work_queue.put(self.agents[0].reddit.subreddit(subreddit))
                
                # Variable delay between queue additions
                time.sleep(random.uniform(1800, 3600))  # 30-60 minutes
                
            except Exception as e:
                logger.error(f"Main loop error: {str(e)}")
                time.sleep(300)

if __name__ == "__main__":
    controller = NetworkController(num_agents=200)
    controller.run()
