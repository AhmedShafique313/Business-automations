import os
import json
import time
import random
import logging
import pandas as pd
import requests
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote
import ssl
import urllib3
import re
import asyncio
from playwright.async_api import async_playwright, Playwright
from bs4 import BeautifulSoup
from .models.model_interface import ModelInterface
from .asana_manager import AsanaManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ListBuildingAgent:
    def __init__(self):
        """Initialize the list building agent"""
        self.setup_logging()
        self.model_interface = ModelInterface()
        self.asana_manager = AsanaManager()
        self.database_file = 'luxury_agents_database.csv'
        self.agent_database = self._load_database()
        self.locations = [
            'Toronto', 'Mississauga', 'Oakville', 'Richmond Hill',
            'Markham', 'Vaughan', 'King City', 'Forest Hill',
            'Rosedale', 'Yorkville'
        ]
        self.playwright = None
        self.browser = None
        self.browser_context = None
        self.page = None
        
        # Add columns for social media handles
        self.columns = [
            'name', 'brokerage', 'phone', 'location', 'description', 
            'instagram_handle', 'facebook_handle', 'linkedin_url', 'telegram_handle',
            'source', 'date_found', 'asana_task_id'
        ]

    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('list_building.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ListBuildingAgent')

    async def setup_browser(self):
        """Set up browser for web scraping"""
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()
            if not self.browser:
                self.browser = await self.playwright.chromium.launch(headless=True)
            if not self.browser_context:
                self.browser_context = await self.browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
            if not self.page:
                self.page = await self.browser_context.new_page()
            self.logger.info("Browser setup completed successfully")
        except Exception as e:
            self.logger.error(f"Error setting up browser: {str(e)}")
            await self.cleanup()
            raise

    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.browser_context:
                await self.browser_context.close()
                self.browser_context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    def _load_database(self):
        """Load existing database or create new one"""
        if os.path.exists(self.database_file):
            try:
                return pd.read_csv(self.database_file)
            except pd.errors.EmptyDataError:
                return pd.DataFrame(columns=self.columns)
        else:
            return pd.DataFrame(columns=self.columns)

    def random_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay between API calls"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    async def search_google(self, query: str) -> List[Dict]:
        """Search Google using browser automation"""
        try:
            # Ensure browser is set up
            if not self.page:
                await self.setup_browser()
                
            # Format query for Google search
            search_url = f"https://www.google.com/search?q={quote(query)}"
            
            # Navigate to search page
            await self.page.goto(search_url)
            await asyncio.sleep(2)  # Wait for results to load
            
            # Extract search results
            results = []
            
            # Wait for and get all search result divs
            search_results = await self.page.query_selector_all("div[data-hveid]")
            
            for result in search_results:
                try:
                    # Get title and link
                    title_elem = await result.query_selector("h3")
                    if not title_elem:
                        continue
                        
                    title = await title_elem.inner_text()
                    
                    # Get URL
                    link_elem = await result.query_selector("a")
                    if not link_elem:
                        continue
                        
                    url = await link_elem.get_attribute("href")
                    if not url or not url.startswith("http"):
                        continue
                    
                    # Get snippet
                    snippet = ""
                    snippet_elem = await result.query_selector("div[style*='line-height']")
                    if snippet_elem:
                        snippet = await snippet_elem.inner_text()
                    
                    if title and url:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet
                        })
                except Exception as e:
                    self.logger.error(f"Error parsing search result: {str(e)}")
                    continue
            
            return results[:10]  # Return top 10 results
            
        except Exception as e:
            self.logger.error(f"Error searching Google: {str(e)}")
            await self.cleanup()  # Cleanup on error
            return []

    async def extract_agent_data(self, result):
        """Extract agent data from search result"""
        try:
            # Extract agent info from search result
            agent_data = {
                'name': result['title'],
                'description': result['snippet'],
                'location': 'Toronto',  # Default location
                'source': result['url'],
                'date_found': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Analyze profile
            analysis = await self.model_interface.analyze_agent(agent_data)
            
            # Add to database if luxury score is high enough
            if analysis.get('luxury_score', 0) >= 70:
                # Create Asana task
                task_created = self.asana_manager.create_task_for_agent(agent_data)
                if task_created:
                    self.logger.info(f"Created Asana task for agent: {agent_data['name']}")
                    agent_data['asana_task_id'] = task_created
                else:
                    self.logger.error(f"Failed to create Asana task for agent: {agent_data['name']}")
                
                # Add to database
                self.agent_database = pd.concat([
                    self.agent_database,
                    pd.DataFrame([agent_data])
                ], ignore_index=True)
                
                # Save after each new addition
                self.agent_database.to_csv(self.database_file, index=False)
                
            return agent_data
            
        except Exception as e:
            self.logger.error(f"Error processing result: {str(e)}")
            return None

    async def run(self, location: Optional[str] = None):
        """Run the list building agent"""
        try:
            location = location or random.choice(self.locations)
            self.logger.info(f"Searching for luxury agents in {location}")
            
            # Set up browser
            await self.setup_browser()
            
            # Search queries
            queries = [
                f"luxury real estate agent {location}",
                f"top realtor {location} luxury homes",
                f"high end real estate agent {location}",
                f"premium property realtor {location}"
            ]
            
            for query in queries:
                try:
                    results = await self.search_google(query)
                    for result in results:
                        agent_data = await self.extract_agent_data(result)
                        if agent_data:
                            self.logger.info(f"Found new agent: {agent_data['name']}")
                        await self.random_delay(2, 5)
                except Exception as e:
                    self.logger.error(f"Error processing query '{query}': {str(e)}")
                    continue
                
        except Exception as e:
            self.logger.error(f"Error running list building agent: {str(e)}")
        finally:
            await self.cleanup()

if __name__ == "__main__":
    # Initialize agent
    agent = ListBuildingAgent()
    
    # Run event loop
    asyncio.run(agent.run())
