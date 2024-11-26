import os
import logging
from typing import Dict, List, Optional
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from playwright.async_api import async_playwright
import json
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus

class DataEnrichmentManager:
    def __init__(self):
        self.setup_logging()
        self.session = None
        self.browser = None
        
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data_enrichment.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('DataEnrichment')

    async def setup(self):
        """Initialize async session and browser"""
        self.session = aiohttp.ClientSession()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def enrich_agent_data(self, agent_data: Dict) -> Dict:
        """Enrich agent data with additional information"""
        try:
            # Initialize enriched data
            enriched_data = agent_data.copy()
            
            # Gather data from multiple sources
            tasks = [
                self._get_social_media_data(agent_data),
                self._get_real_estate_data(agent_data),
                self._get_contact_data(agent_data)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Combine results
            for result in results:
                enriched_data.update(result)
            
            return enriched_data
            
        except Exception as e:
            self.logger.error(f"Error enriching agent data: {str(e)}")
            return agent_data

    async def _get_social_media_data(self, agent_data: Dict) -> Dict:
        """Get social media information using web scraping"""
        social_data = {}
        try:
            name = agent_data.get('name', '')
            location = agent_data.get('location', '')
            
            # Search for LinkedIn profile
            linkedin_data = await self._scrape_linkedin_public(name, location)
            if linkedin_data:
                social_data['linkedin'] = linkedin_data
            
            # Search for Instagram business profile
            instagram_data = await self._scrape_instagram_public(name, location)
            if instagram_data:
                social_data['instagram'] = instagram_data
            
            # Search for real estate related tweets
            twitter_data = await self._search_twitter(name, location)
            if twitter_data:
                social_data['twitter'] = twitter_data
            
            return social_data
            
        except Exception as e:
            self.logger.error(f"Error getting social media data: {str(e)}")
            return {}

    async def _get_real_estate_data(self, agent_data: Dict) -> Dict:
        """Get real estate information from public sources"""
        try:
            name = agent_data.get('name', '')
            location = agent_data.get('location', '')
            
            # Search real estate websites
            tasks = [
                self._scrape_realtor_public(name, location)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Combine results
            real_estate_data = {}
            for result in results:
                real_estate_data.update(result)
            
            return real_estate_data
            
        except Exception as e:
            self.logger.error(f"Error getting real estate data: {str(e)}")
            return {}

    async def _get_contact_data(self, agent_data: Dict) -> Dict:
        """Get and verify contact information"""
        try:
            # Use email-verifier library for basic validation
            email = agent_data.get('email', '')
            if email:
                email_valid = self._verify_email_format(email)
                if not email_valid:
                    self.logger.warning(f"Invalid email format: {email}")
            
            # Validate phone number format
            phone = agent_data.get('phone', '')
            if phone:
                phone_valid = self._verify_phone_format(phone)
                if not phone_valid:
                    self.logger.warning(f"Invalid phone format: {phone}")
            
            return {
                'email_valid': email_valid if email else None,
                'phone_valid': phone_valid if phone else None
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying contact data: {str(e)}")
            return {}

    async def _scrape_linkedin_public(self, name: str, location: str) -> Dict:
        """Scrape public LinkedIn profile information"""
        try:
            search_query = f"{name} {location} real estate agent site:linkedin.com/in/"
            page = await self.browser.new_page()
            await page.goto(f"https://www.google.com/search?q={quote_plus(search_query)}")
            
            # Extract LinkedIn URL
            linkedin_url = await page.query_selector("a[href*='linkedin.com/in/']")
            if linkedin_url:
                url = await linkedin_url.get_attribute('href')
                
                # Visit LinkedIn profile
                await page.goto(url)
                
                # Extract public information
                data = {
                    'profile_url': url,
                    'headline': await self._extract_text(page, '.top-card-layout__headline'),
                    'location': await self._extract_text(page, '.top-card-layout__location'),
                    'experience': await self._extract_experience(page),
                    'education': await self._extract_education(page)
                }
                
                await page.close()
                return data
                
        except Exception as e:
            self.logger.error(f"Error scraping LinkedIn: {str(e)}")
            return {}

    async def _scrape_instagram_public(self, name: str, location: str) -> Dict:
        """Scrape public Instagram business profile information"""
        try:
            search_query = f"{name} {location} real estate instagram"
            page = await self.browser.new_page()
            await page.goto(f"https://www.google.com/search?q={quote_plus(search_query)}")
            
            # Extract Instagram URL
            instagram_url = await page.query_selector("a[href*='instagram.com/']")
            if instagram_url:
                url = await instagram_url.get_attribute('href')
                
                # Visit Instagram profile
                await page.goto(url)
                
                # Extract public information
                data = {
                    'profile_url': url,
                    'bio': await self._extract_text(page, '.-vDIg'),
                    'posts_count': await self._extract_text(page, '.g47SY'),
                    'business_category': await self._extract_text(page, '.K5OFK')
                }
                
                await page.close()
                return data
                
        except Exception as e:
            self.logger.error(f"Error scraping Instagram: {str(e)}")
            return {}

    async def _search_twitter(self, name: str, location: str) -> Dict:
        """Search for real estate related tweets"""
        try:
            search_query = f"{name} {location} real estate"
            page = await self.browser.new_page()
            await page.goto(f"https://twitter.com/search?q={quote_plus(search_query)}&f=live")
            
            # Extract recent tweets
            tweets = await page.query_selector_all("[data-testid='tweet']")
            tweet_data = []
            
            for tweet in tweets[:5]:  # Get last 5 tweets
                tweet_text = await self._extract_text(tweet, "[data-testid='tweetText']")
                tweet_date = await self._extract_text(tweet, "time")
                
                if tweet_text:
                    tweet_data.append({
                        'text': tweet_text,
                        'date': tweet_date
                    })
            
            await page.close()
            return {'recent_tweets': tweet_data}
            
        except Exception as e:
            self.logger.error(f"Error searching Twitter: {str(e)}")
            return {}

    async def _scrape_realtor_public(self, name: str, location: str) -> Dict:
        """Scrape public Realtor.com profile information"""
        try:
            search_query = f"{name} {location} site:realtor.com/realestateagents/"
            page = await self.browser.new_page()
            await page.goto(f"https://www.google.com/search?q={quote_plus(search_query)}")
            
            # Extract Realtor.com URL
            realtor_url = await page.query_selector("a[href*='realtor.com/realestateagents/']")
            if realtor_url:
                url = await realtor_url.get_attribute('href')
                
                # Visit Realtor.com profile
                await page.goto(url)
                
                # Extract public information
                data = {
                    'profile_url': url,
                    'active_listings': await self._extract_text(page, '.agent-detail-stats'),
                    'specialties': await self._extract_list(page, '.agent-specialties li'),
                    'areas_served': await self._extract_list(page, '.agent-areas-served li')
                }
                
                await page.close()
                return data
                
        except Exception as e:
            self.logger.error(f"Error scraping Realtor.com: {str(e)}")
            return {}

    def _verify_email_format(self, email: str) -> bool:
        """Verify email format using regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _verify_phone_format(self, phone: str) -> bool:
        """Verify phone number format"""
        # Remove all non-numeric characters
        clean_number = ''.join(filter(str.isdigit, phone))
        # Check if the number has 10-15 digits
        return 10 <= len(clean_number) <= 15

    async def _extract_text(self, element, selector: str) -> str:
        """Extract text from an element"""
        try:
            el = await element.query_selector(selector)
            if el:
                return await el.text_content()
            return ''
        except Exception:
            return ''

    async def _extract_list(self, element, selector: str) -> List[str]:
        """Extract list of text items"""
        try:
            elements = await element.query_selector_all(selector)
            return [await el.text_content() for el in elements]
        except Exception:
            return []

    async def _extract_experience(self, page) -> List[Dict]:
        """Extract work experience from LinkedIn"""
        try:
            experience_items = await page.query_selector_all('#experience-section li')
            experience = []
            
            for item in experience_items:
                title = await self._extract_text(item, '.pv-entity__summary-info h3')
                company = await self._extract_text(item, '.pv-entity__secondary-title')
                dates = await self._extract_text(item, '.pv-entity__date-range span:nth-child(2)')
                
                if title:
                    experience.append({
                        'title': title,
                        'company': company,
                        'dates': dates
                    })
            
            return experience
        except Exception:
            return []

    async def _extract_education(self, page) -> List[Dict]:
        """Extract education from LinkedIn"""
        try:
            education_items = await page.query_selector_all('#education-section li')
            education = []
            
            for item in education_items:
                school = await self._extract_text(item, '.pv-entity__school-name')
                degree = await self._extract_text(item, '.pv-entity__degree-name span:nth-child(2)')
                field = await self._extract_text(item, '.pv-entity__fos span:nth-child(2)')
                
                if school:
                    education.append({
                        'school': school,
                        'degree': degree,
                        'field': field
                    })
            
            return education
        except Exception:
            return []
