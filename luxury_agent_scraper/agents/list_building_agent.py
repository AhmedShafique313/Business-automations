import os
import re
import json
import random
import asyncio
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List
from urllib.parse import quote, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page

from ..utils.errors import *
from ..utils.validation import validate_agent_data
from ..utils.rate_limiter import AdaptiveRateLimiter

class ListBuildingAgent:
    def __init__(self, model_interface):
        """Initialize the list building agent"""
        self.setup_logging()
        self.model_interface = model_interface
        
        # Initialize rate limiters
        self.search_limiter = AdaptiveRateLimiter(10, 60)  # 10 searches per minute
        self.scrape_limiter = AdaptiveRateLimiter(30, 60)  # 30 scrapes per minute
        
        # Initialize database columns
        self.columns = [
            'name', 'brokerage', 'email', 'phone', 'location', 'description',
            'instagram_handle', 'facebook_handle', 'linkedin_url', 'twitter_handle',
            'website_url', 'source_url', 'date_found', 'luxury_score',
            'analysis', 'recommendations', 'asana_ready'
        ]
        
        # Set up database path
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.database_file = os.path.join(self.data_dir, 'luxury_agents_database.csv')
        self.agent_database = self._load_database()
        
        # Configure search locations
        self.locations = [
            'Toronto', 'Mississauga', 'Oakville', 'Richmond Hill',
            'Markham', 'Vaughan', 'King City', 'Forest Hill',
            'Rosedale', 'Yorkville'
        ]
        
        # Search queries per location
        self.search_queries = [
            "luxury real estate agent",
            "high end realtor",
            "premium property agent",
            "luxury homes specialist",
            "exclusive real estate agent"
        ]
        
        # Configure delays
        self.min_delay = 2
        self.max_delay = 5
    
    def setup_logging(self):
        """Set up logging configuration"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Create handlers
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler('agent.log')
        c_handler.setLevel(logging.INFO)
        f_handler.setLevel(logging.INFO)
        
        # Create formatters and add it to handlers
        log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(log_format)
        f_handler.setFormatter(log_format)
        
        # Add handlers to the logger
        self.logger.addHandler(c_handler)
        self.logger.addHandler(f_handler)
    
    def _load_database(self) -> pd.DataFrame:
        """Load or create agent database"""
        try:
            if os.path.exists(self.database_file):
                return pd.read_csv(self.database_file)
            return pd.DataFrame(columns=self.columns)
        except Exception as e:
            self.logger.error(f"Error loading database: {str(e)}")
            return pd.DataFrame(columns=self.columns)
    
    def save_database(self):
        """Save agent database to CSV"""
        try:
            self.agent_database.to_csv(self.database_file, index=False)
        except Exception as e:
            self.logger.error(f"Error saving database: {str(e)}")
    
    async def setup_browser(self):
        """Set up browser context"""
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            return browser
        except Exception as e:
            self.logger.error(f"Error setting up browser: {str(e)}")
            raise
    
    async def search_agents(self, page: Page, search_query: str) -> List[Dict]:
        """Search for agents using the provided search query"""
        results = []
        
        try:
            # Apply rate limiting
            domain = "google.com"
            try:
                await self.search_limiter.acquire(domain)
            except RateLimitError as e:
                self.logger.warning(str(e))
                await asyncio.sleep(5)  # Wait before retry
                await self.search_limiter.acquire(domain)
            
            self.logger.info(f"Searching: {search_query}")
            
            # Perform Google search
            await page.goto(f"https://www.google.com/search?q={quote(search_query)}")
            await page.wait_for_selector("div#search")
            
            # Extract search results
            search_results = await page.query_selector_all("div.g")
            
            for result in search_results[:5]:  # Process top 5 results
                try:
                    title_elem = await result.query_selector("h3")
                    description_elem = await result.query_selector("div.VwiC3b")
                    link_elem = await result.query_selector("a")
                    
                    if title_elem and description_elem and link_elem:
                        title = await title_elem.inner_text()
                        description = await description_elem.inner_text()
                        link = await link_elem.get_attribute("href")
                        
                        # Skip if not a real estate agent website
                        if any(x in link.lower() for x in ['wikipedia', 'news', 'article', 'blog']):
                            continue
                        
                        results.append({
                            'title': title,
                            'description': description,
                            'link': link
                        })
                        
                except Exception as e:
                    self.logger.error(f"Error processing search result: {str(e)}")
                    continue
            
            # Random delay between searches
            delay = random.uniform(self.min_delay, self.max_delay)
            await asyncio.sleep(delay)
            
        except Exception as e:
            self.logger.error(f"Error in search_agents: {str(e)}")
            if isinstance(e, RateLimitError):
                raise
        
        return results
    
    async def extract_contact_info(self, page: Page, url: str) -> Dict:
        """Extract contact information from agent's page"""
        contact_info = {
            'email': '',
            'phone': '',
            'instagram_handle': '',
            'facebook_handle': '',
            'linkedin_url': '',
            'twitter_handle': '',
            'website_url': url
        }
        
        try:
            # Apply rate limiting
            domain = urlparse(url).netloc
            try:
                await self.scrape_limiter.acquire(domain)
            except RateLimitError as e:
                self.logger.warning(str(e))
                await asyncio.sleep(5)  # Wait before retry
                await self.scrape_limiter.acquire(domain)
            
            # Visit the page with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await page.goto(url, timeout=30000, wait_until='networkidle')
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise ScrapingError(f"Failed to load page after {max_retries} attempts: {str(e)}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract email addresses with better pattern
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, content)
            if emails:
                # Filter out common false positives
                valid_emails = [e for e in emails if not any(x in e.lower() for x in ['example', 'domain', '@site'])]
                if valid_emails:
                    contact_info['email'] = valid_emails[0]
            
            # Extract phone numbers with better pattern
            phone_pattern = r'(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})'
            phones = re.findall(phone_pattern, content)
            if phones:
                contact_info['phone'] = f"{''.join(phones[0])}"
            
            # Extract social media handles with validation
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                if 'instagram.com' in href and '/p/' not in href:  # Exclude individual posts
                    contact_info['instagram_handle'] = href
                elif 'facebook.com' in href and not href.endswith('facebook.com'):
                    contact_info['facebook_handle'] = href
                elif 'linkedin.com/in/' in href:  # Only capture profile URLs
                    contact_info['linkedin_url'] = href
                elif 'twitter.com' in href and not any(x in href for x in ['status', 'tweet']):
                    contact_info['twitter_handle'] = href
            
        except Exception as e:
            if isinstance(e, ScrapingError):
                raise
            self.logger.error(f"Error extracting contact info from {url}: {str(e)}")
        
        return contact_info
    
    def _extract_agent_info(self, title: str, description: str, url: str, location: str) -> Dict:
        """Extract agent information from search result"""
        try:
            # Basic info
            name = title.split('-')[0].strip() if '-' in title else title.strip()
            brokerage = title.split('-')[1].strip() if '-' in title else ''
            
            # Clean up name and brokerage
            name = re.sub(r'\|.*$', '', name).strip()
            brokerage = re.sub(r'\|.*$', '', brokerage).strip()
            
            return {
                'name': name,
                'brokerage': brokerage,
                'description': description,
                'location': location
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting agent info: {str(e)}")
            return None
    
    def _is_duplicate(self, agent_info: Dict) -> bool:
        """Check if agent already exists in database"""
        if agent_info['name'] in self.agent_database['name'].values:
            return True
        return False
    
    def _prepare_for_asana(self, agent_data: Dict) -> Dict:
        """Prepare agent data for Asana"""
        return {
            'name': agent_data['name'],
            'notes': f"""
                Brokerage: {agent_data['brokerage']}
                Location: {agent_data['location']}
                Email: {agent_data['email']}
                Phone: {agent_data['phone']}
                Website: {agent_data['website_url']}
                LinkedIn: {agent_data['linkedin_url']}
                Instagram: {agent_data['instagram_handle']}
                Facebook: {agent_data['facebook_handle']}
                Twitter: {agent_data['twitter_handle']}
                
                Description:
                {agent_data['description']}
                
                Analysis:
                {agent_data['analysis']}
                
                Recommendations:
                {agent_data['recommendations']}
                
                Luxury Score: {agent_data['luxury_score']}
            """.strip()
        }
    
    async def discover_agents(self, location: str) -> List[Dict]:
        """Discover luxury real estate agents in a given location"""
        agents_data = []
        
        try:
            # Create browser context
            browser_context = await self.setup_browser()
            async with browser_context as browser:
                page = await browser.new_page()
                
                for query in self.search_queries:
                    search_query = f"{query} {location}"
                    
                    try:
                        # Search for agents
                        results = await self.search_agents(page, search_query)
                        
                        for result in results:
                            try:
                                # Extract agent info
                                agent_info = self._extract_agent_info(
                                    result['title'],
                                    result['description'],
                                    result['link'],
                                    location
                                )
                                
                                if agent_info and not self._is_duplicate(agent_info):
                                    # Get contact information
                                    contact_info = await self.extract_contact_info(page, result['link'])
                                    
                                    # Create agent data
                                    agent_data = {
                                        'name': agent_info['name'],
                                        'brokerage': agent_info['brokerage'],
                                        'title': result['title'],
                                        'description': result['description'],
                                        'url': result['link'],
                                        'location': location,
                                        'contact_info': json.dumps(contact_info),
                                        'search_query': search_query
                                    }
                                    
                                    try:
                                        # Analyze with OpenAI
                                        analysis = await self.model_interface.analyze_agent(agent_data)
                                        agent_data.update(analysis)
                                    except APIError as e:
                                        self.logger.error(f"API error analyzing agent: {str(e)}")
                                        continue
                                    
                                    # Prepare for Asana
                                    asana_data = self._prepare_for_asana(agent_data)
                                    agent_data['asana_ready'] = json.dumps(asana_data)
                                    
                                    # Add to database
                                    self.agent_database = pd.concat([
                                        self.agent_database, 
                                        pd.DataFrame([agent_data])
                                    ], ignore_index=True)
                                    
                                    # Save after each agent
                                    self.save_database()
                                    
                                    agents_data.append(agent_data)
                                    self.logger.info(f"Found agent: {agent_data['name']}")
                                    
                            except Exception as e:
                                self.logger.error(f"Error processing agent: {str(e)}")
                                continue
                    except Exception as e:
                        self.logger.error(f"Error searching agents: {str(e)}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error in discover_agents: {str(e)}")
            
        return agents_data
