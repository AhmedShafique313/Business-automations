import praw
import json
import time
import random
from datetime import datetime, timedelta
import threading
import queue
import logging
from typing import List, Dict
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedditAgent:
    def __init__(self, credentials: Dict, agent_id: int):
        self.agent_id = agent_id
        self.reddit = praw.Reddit(
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret'],
            user_agent=f"DesignGaga_{agent_id}",
            username=credentials['username'],
            password=credentials['password']
        )
        
        self.daily_comments = 0
        self.weekly_comments = 0
        self.last_reset = datetime.now()
        self.last_weekly_reset = datetime.now()
        self.recent_posts = set()
        
        # Randomize personality traits
        self.chattiness = random.uniform(0.6, 0.9)  # How likely to comment
        self.formality = random.uniform(0.3, 0.8)   # How formal the language is
        
    def get_response_style(self):
        """Generate personality-specific response templates"""
        if self.formality > 0.6:
            intros = [
                "I noticed your post. ",
                "Regarding your question, ",
                "I can offer some insight. ",
                "Based on my experience, ",
                "This is interesting. "
            ]
        else:
            intros = [
                "Hey! ",
                "Quick tip - ",
                "Here's what worked for me: ",
                "Just my 2 cents: ",
                "Thought I'd share: "
            ]
        return random.choice(intros)

class MultiAgentController:
    def __init__(self, num_agents: int = 100):
        self.num_agents = num_agents
        self.agents: List[RedditAgent] = []
        self.work_queue = queue.Queue()
        self.load_agents()
        
    def load_agents(self):
        """Initialize multiple Reddit agents with different credentials"""
        try:
            with open("../credentials.json", 'r') as f:
                creds = json.load(f)
                
            # Load base credentials
            base_creds = creds['REDDIT']
            
            # Create variations for multiple agents
            for i in range(self.num_agents):
                agent_creds = base_creds.copy()
                agent_creds['username'] = f"{base_creds['username']}_{i}"
                agent = RedditAgent(agent_creds, i)
                self.agents.append(agent)
                
            logger.info(f"Successfully initialized {len(self.agents)} agents")
        except Exception as e:
            logger.error(f"Failed to load agents: {str(e)}")

    def create_natural_response(self, agent: RedditAgent, topic: str) -> str:
        """Create a human-like response with agent-specific personality"""
        intro = agent.get_response_style()
        
        # Topic-specific advice with personality variation
        if "staging" in topic.lower():
            advice = random.choice([
                "decluttering really opens up the space",
                "neutral colors are your best friend",
                "less is definitely more when staging",
                "focus on the key selling areas"
            ])
        elif "selling" in topic.lower():
            advice = random.choice([
                "pricing right from day one is crucial",
                "first impressions matter a lot",
                "professional photos make a huge difference",
                "timing the market can be key"
            ])
        else:
            advice = random.choice([
                "small updates can transform a space",
                "lighting changes everything",
                "fresh paint works wonders",
                "focus on curb appeal first"
            ])
        
        # Randomize website mention (based on agent chattiness)
        if random.random() < agent.chattiness:
            website = f" Check out designgaga.ca/tips/{random.choice(['staging', 'selling', 'design'])} for more ideas."
        else:
            website = ""
        
        closing = random.choice([
            "Hope this helps!",
            "Good luck!",
            "Let me know if you need more info.",
            "Happy to help further."
        ])
        
        return f"{intro}{advice}.{website} {closing}"

    def should_engage(self, agent: RedditAgent, post) -> bool:
        """Determine if agent should engage with post"""
        # Check agent-specific limits
        if post.id in agent.recent_posts:
            return False
            
        # Reset counters if needed
        current_time = datetime.now()
        if (current_time - agent.last_reset).days >= 1:
            agent.daily_comments = 0
            agent.last_reset = current_time
            
        if (current_time - agent.last_weekly_reset).days >= 7:
            agent.weekly_comments = 0
            agent.last_weekly_reset = current_time
        
        # Check limits
        if agent.daily_comments >= 8:  # Conservative daily limit
            return False
        if agent.weekly_comments >= 40:  # Conservative weekly limit
            return False
            
        # Post-specific checks
        post_age = current_time - datetime.fromtimestamp(post.created_utc)
        if post_age > timedelta(hours=24):
            return False
        
        if post.num_comments > 50:
            return False
            
        # Personality-based decision
        return random.random() < agent.chattiness

    def agent_worker(self, agent: RedditAgent):
        """Worker function for each agent thread"""
        while True:
            try:
                subreddit = self.work_queue.get()
                if subreddit is None:
                    break
                
                for post in subreddit.new(limit=3):
                    if self.should_engage(agent, post):
                        response = self.create_natural_response(agent, post.title)
                        post.reply(response)
                        
                        agent.recent_posts.add(post.id)
                        agent.daily_comments += 1
                        agent.weekly_comments += 1
                        
                        # Random delay between comments (2-6 hours)
                        time.sleep(random.uniform(7200, 21600))
                        
            except Exception as e:
                logger.error(f"Agent {agent.agent_id} error: {str(e)}")
                time.sleep(300)
            finally:
                self.work_queue.task_done()

    def run(self):
        """Start the multi-agent system"""
        subreddits = [
            "RealEstate", "HomeImprovement", "InteriorDesign",
            "RealEstateInvesting", "HomeDecorating", "RealEstateCanada"
        ]
        
        # Start agent threads
        threads = []
        for agent in self.agents:
            t = threading.Thread(target=self.agent_worker, args=(agent,))
            t.start()
            threads.append(t)
        
        # Main monitoring loop
        while True:
            try:
                # Randomly select subreddit and add to work queue
                subreddit = random.choice(subreddits)
                self.work_queue.put(self.agents[0].reddit.subreddit(subreddit))
                
                # Add delay between queue additions
                time.sleep(random.uniform(3600, 7200))  # 1-2 hours
                
            except Exception as e:
                logger.error(f"Main loop error: {str(e)}")
                time.sleep(300)

if __name__ == "__main__":
    controller = MultiAgentController(num_agents=100)
    controller.run()
