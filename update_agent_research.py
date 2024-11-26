import os
import json
import logging
import asyncio
from typing import Dict, Optional, List
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from agents.asana_manager import AsanaManager
from urllib.parse import quote
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Serper API configuration
SERPER_API_KEY = "0b81106d9502cda4d502c95921feeeb80619fbb965c916a8c8def4e2537c1e1e"
SERPER_API_URL = "https://google.serper.dev/search"

class AgentResearcher:
    """Class to handle agent research operations."""
    
    def __init__(self):
        self.headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
    
    async def search_with_serper(self, query: str) -> List[Dict]:
        """Perform a search using Serper API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    SERPER_API_URL,
                    headers=self.headers,
                    json={
                        'q': query,
                        'gl': 'ca',  # Canada
                        'hl': 'en',  # English
                        'num': 10    # Number of results
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data.get('organic', [])
        except Exception as e:
            logger.error(f"Serper API error: {str(e)}")
            return []

    async def research_social_profiles(self, agent_name: str, location: str = None) -> Dict:
        """Research all social media profiles for an agent."""
        profiles = {
            'linkedin': None,
            'instagram': None,
            'facebook': None,
            'twitter': None,
            'zillow': None,
            'realtor': None,
            'youtube': None
        }
        
        search_queries = [
            f"{agent_name} real estate agent linkedin",
            f"{agent_name} realtor instagram",
            f"{agent_name} real estate facebook",
            f"{agent_name} realtor twitter",
            f"{agent_name} zillow profile",
            f"{agent_name} realtor.com profile",
            f"{agent_name} real estate youtube"
        ]
        
        if location:
            search_queries = [f"{query} {location}" for query in search_queries]
        
        for query, platform in zip(search_queries, profiles.keys()):
            try:
                results = await self.search_with_serper(query)
                
                for result in results:
                    link = result.get('link', '')
                    if platform.lower() in link.lower():
                        profiles[platform] = link
                        break
                
                # Add a small delay between searches
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error searching for {platform} profile: {str(e)}")
        
        return profiles

    async def get_detailed_listings(self, agent_name: str, location: str = None) -> List[Dict]:
        """Get detailed information about agent's current listings."""
        listings = []
        search_sites = [
            'zillow.com',
            'realtor.com',
            'redfin.com',
            'trulia.com'
        ]
        
        for site in search_sites:
            try:
                search_query = f"{agent_name} real estate agent listings {site}"
                if location:
                    search_query += f" {location}"
                
                results = await self.search_with_serper(search_query)
                
                for result in results:
                    try:
                        link = result.get('link', '')
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        
                        if site in link.lower():
                            # Extract price if available
                            price_match = re.search(r'\$[\d,]+(?:,\d{3})*', snippet)
                            price = price_match.group(0) if price_match else None
                            
                            # Extract address if available
                            address_pattern = r'\d+\s+[A-Za-z\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)'
                            address_match = re.search(address_pattern, snippet, re.IGNORECASE)
                            address = address_match.group(0) if address_match else None
                            
                            listings.append({
                                'title': title,
                                'link': link,
                                'description': snippet,
                                'price': price,
                                'address': address,
                                'source': site,
                                'found_date': datetime.now().strftime('%Y-%m-%d')
                            })
                    except Exception as e:
                        logger.warning(f"Error processing listing result: {str(e)}")
                        continue
                
                # Add a small delay between searches
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error searching listings on {site}: {str(e)}")
        
        return listings

    async def analyze_personality(self, social_profiles: Dict, listings: List[Dict]) -> Dict:
        """Analyze agent's personality based on their social media content and listings."""
        personality = {
            'communication_style': 'Unknown',
            'content_focus': [],
            'engagement_level': 'Unknown'
        }
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                page = await context.new_page()
                await page.set_default_timeout(15000)
                
                # Analyze LinkedIn content
                if social_profiles.get('linkedin'):
                    try:
                        await page.goto(social_profiles['linkedin'], wait_until='domcontentloaded')
                        content = await page.content()
                        
                        # Basic content analysis
                        content_lower = content.lower()
                        
                        # Determine communication style
                        if any(word in content_lower for word in ['luxury', 'exclusive', 'premium']):
                            personality['communication_style'] = 'Professional and upscale'
                            personality['content_focus'].append('Luxury market')
                        elif any(word in content_lower for word in ['family', 'community', 'home']):
                            personality['communication_style'] = 'Warm and personal'
                            personality['content_focus'].append('Community focus')
                        else:
                            personality['communication_style'] = 'Professional and informative'
                            personality['content_focus'].append('General real estate')
                        
                    except Exception as e:
                        logger.warning(f"Error analyzing LinkedIn: {str(e)}")
                
                # Analyze Instagram content
                if social_profiles.get('instagram'):
                    try:
                        await page.goto(social_profiles['instagram'], wait_until='domcontentloaded')
                        content = await page.content()
                        
                        # Basic engagement analysis
                        engagement_indicators = ['followers', 'following', 'posts']
                        if any(indicator in content.lower() for indicator in engagement_indicators):
                            personality['engagement_level'] = 'Active on social media'
                        
                    except Exception as e:
                        logger.warning(f"Error analyzing Instagram: {str(e)}")
                
                await context.close()
                await browser.close()
                
        except Exception as e:
            logger.error(f"Error in personality analysis: {str(e)}")
        
        return personality

    async def extract_contact_info(self, social_profiles: Dict, listings: List[Dict]) -> Dict:
        """Extract agent's contact information from social media profiles and listings."""
        contact_info = {
            'email': None,
            'phone': None,
            'office': None
        }
        
        # Extract from social profiles
        for profile_url in social_profiles.values():
            if not profile_url:
                continue
                
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(profile_url)
                    content = response.text
                    
                    # Extract email
                    if not contact_info['email']:
                        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                        if email_match:
                            contact_info['email'] = email_match.group(0)
                    
                    # Extract phone
                    if not contact_info['phone']:
                        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', content)
                        if phone_match:
                            contact_info['phone'] = phone_match.group(0)
                    
                    # Extract office
                    if not contact_info['office']:
                        office_pattern = r'(?:Office|Location):\s*([^<>\n]+)'
                        office_match = re.search(office_pattern, content)
                        if office_match:
                            contact_info['office'] = office_match.group(1).strip()
                
            except Exception as e:
                logger.warning(f"Error extracting contact info from profile: {str(e)}")
        
        # Extract from listings
        for listing in listings:
            if not contact_info['phone']:
                phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', listing.get('description', ''))
                if phone_match:
                    contact_info['phone'] = phone_match.group(0)
            
            if not contact_info['email']:
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', listing.get('description', ''))
                if email_match:
                    contact_info['email'] = email_match.group(0)
        
        return contact_info

async def update_agent_task(client: AsanaManager, task_gid: str, agent_name: str):
    """Update agent task with comprehensive research."""
    try:
        # Get agent's location from task description if available
        task_info = client.client.tasks.get_task(task_gid)
        location = None
        if 'notes' in task_info:
            location_match = re.search(r'Location:\s*(.+?)(?:\n|$)', task_info['notes'])
            if location_match:
                location = location_match.group(1)
        
        logger.info(f"Researching agent: {agent_name} ({location if location else 'no location'})")
        
        # Initialize researcher
        researcher = AgentResearcher()
        
        # Gather comprehensive research
        profiles = await researcher.research_social_profiles(agent_name, location)
        logger.info(f"Found {sum(1 for p in profiles.values() if p)} social profiles")
        
        listings = await researcher.get_detailed_listings(agent_name, location)
        logger.info(f"Found {len(listings)} listings")
        
        personality = await researcher.analyze_personality(profiles, listings)
        contact_info = await researcher.extract_contact_info(profiles, listings)
        
        research_data = {
            'social_profiles': profiles,
            'listings': listings,
            'personality': personality,
            'contact_info': contact_info,
            'research_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Update task in Asana
        success = client.update_agent_research(task_gid, research_data)
        if success:
            logger.info(f"Successfully updated research for agent: {agent_name}")
        else:
            logger.error(f"Failed to update research for agent: {agent_name}")
            
    except Exception as e:
        logger.error(f"Error updating agent task: {str(e)}")

async def main():
    """Update research for all agents in Asana."""
    try:
        # Initialize Asana manager
        asana = AsanaManager()
        
        # Get all tasks from the IPOP.ai project
        tasks = asana.get_all_tasks()
        logger.info(f"Found {len(tasks)} tasks to process")
        
        # Process each task
        for task in tasks:
            try:
                # Extract agent name from task
                task_name = task['name']
                logger.info(f"Processing task: {task_name}")
                
                # Update task with comprehensive research
                await update_agent_task(asana, task['gid'], task_name)
                
                # Add a small delay between agents
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error processing task {task_name}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
    
    finally:
        logger.info("Agent research update completed")
        
        # Clean up browser resources
        if hasattr(asana, 'browser') and asana.browser:
            await asana._close_browser()

if __name__ == "__main__":
    asyncio.run(main())
