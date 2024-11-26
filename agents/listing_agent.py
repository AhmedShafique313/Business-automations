import os
from typing import Dict, List, Optional
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import time
from datetime import datetime, timedelta
import random
from bs4 import BeautifulSoup
import schedule
from asana_tracker import AsanaTracker

class ListingAgent:
    def __init__(self, work_dir: str):
        self.work_dir = work_dir
        self.asana = AsanaTracker(os.getenv('ASANA_WORKSPACE_GID'))
        
        # Load classified sites configuration
        self.sites = {
            'craigslist': {
                'url': 'https://craigslist.org',
                'categories': ['services', 'real estate', 'business'],
                'posting_frequency': timedelta(days=7),
                'max_posts_per_day': 2
            },
            'facebook_marketplace': {
                'url': 'https://facebook.com/marketplace',
                'categories': ['Home Services', 'Real Estate Services'],
                'posting_frequency': timedelta(days=3),
                'max_posts_per_day': 3
            },
            'kijiji': {
                'url': 'https://kijiji.ca',
                'categories': ['Real Estate Services', 'Home Staging'],
                'posting_frequency': timedelta(days=5),
                'max_posts_per_day': 2
            }
        }
        
        # Load listing templates
        self.templates = self._load_templates()
        
        # Initialize webdriver
        self.driver = self._setup_webdriver()
        
        # Track posted listings
        self.listings_file = os.path.join(work_dir, 'data', 'listings.json')
        self.listings = self._load_listings()
        
    def _setup_webdriver(self) -> webdriver.Chrome:
        """Setup Chrome webdriver with proper options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=options)
        
    def _load_templates(self) -> Dict:
        """Load listing templates with variations"""
        templates_dir = os.path.join(self.work_dir, 'templates', 'listings')
        templates = {}
        
        for template_file in os.listdir(templates_dir):
            if template_file.endswith('.json'):
                with open(os.path.join(templates_dir, template_file)) as f:
                    templates[template_file[:-5]] = json.load(f)
                    
        return templates
        
    def _load_listings(self) -> Dict:
        """Load history of posted listings"""
        if os.path.exists(self.listings_file):
            with open(self.listings_file) as f:
                return json.load(f)
        return {'listings': []}
        
    def _save_listings(self):
        """Save listings history"""
        with open(self.listings_file, 'w') as f:
            json.dump(self.listings, f, indent=2)
            
    def create_listing(self, site: str, category: str) -> Dict:
        """Create a new listing with varied content"""
        template = random.choice(self.templates[site])
        
        # Randomize content slightly
        title_variants = template['title_variants']
        description_variants = template['description_variants']
        
        listing = {
            'title': random.choice(title_variants),
            'description': random.choice(description_variants),
            'price_range': template['price_range'],
            'images': template['images'][:4],  # Most sites allow 4 images
            'contact': {
                'name': template['contact']['name'],
                'email': template['contact']['email'],
                'phone': template['contact']['phone']
            },
            'location': template['location'],
            'category': category
        }
        
        return listing
        
    def post_to_craigslist(self, listing: Dict) -> Optional[str]:
        """Post listing to Craigslist"""
        try:
            self.driver.get('https://craigslist.org/post')
            
            # Select category
            category_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//label[contains(text(), '{listing['category']}')]"))
            )
            category_elem.click()
            
            # Fill in listing details
            self.driver.find_element(By.NAME, 'PostingTitle').send_keys(listing['title'])
            self.driver.find_element(By.NAME, 'PostingBody').send_keys(listing['description'])
            self.driver.find_element(By.NAME, 'price').send_keys(listing['price_range'])
            
            # Add images
            for image in listing['images']:
                self.driver.find_element(By.NAME, 'file').send_keys(image)
                time.sleep(2)  # Wait for upload
                
            # Submit and get listing URL
            self.driver.find_element(By.NAME, 'submit').click()
            time.sleep(5)
            
            return self.driver.current_url
            
        except Exception as e:
            print(f"Error posting to Craigslist: {str(e)}")
            return None
            
    def post_to_facebook(self, listing: Dict) -> Optional[str]:
        """Post listing to Facebook Marketplace"""
        try:
            self.driver.get('https://facebook.com/marketplace/create/item')
            
            # Login if needed
            if 'login' in self.driver.current_url:
                self._facebook_login()
                
            # Fill in listing details
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'title'))
            )
            title_input.send_keys(listing['title'])
            
            # Select category
            category_dropdown = self.driver.find_element(By.XPATH, "//span[text()='Select a category']")
            category_dropdown.click()
            category_option = self.driver.find_element(By.XPATH, f"//span[text()='{listing['category']}']")
            category_option.click()
            
            # Add description and price
            self.driver.find_element(By.NAME, 'description').send_keys(listing['description'])
            self.driver.find_element(By.NAME, 'price').send_keys(listing['price_range'].split('-')[0])
            
            # Add images
            for image in listing['images']:
                self.driver.find_element(By.CSS_SELECTOR, '[data-testid="media-upload-input"]').send_keys(image)
                time.sleep(2)
                
            # Submit
            self.driver.find_element(By.XPATH, "//span[text()='Next']").click()
            time.sleep(5)
            
            return self.driver.current_url
            
        except Exception as e:
            print(f"Error posting to Facebook: {str(e)}")
            return None
            
    def run_daily_listings(self):
        """Run daily listing creation across platforms"""
        for site, config in self.sites.items():
            # Check if we can post today
            recent_posts = [
                l for l in self.listings['listings']
                if l['site'] == site and 
                datetime.fromisoformat(l['date']) > datetime.now() - config['posting_frequency']
            ]
            
            if len(recent_posts) >= config['max_posts_per_day']:
                continue
                
            # Create and post new listings
            for category in config['categories']:
                listing = self.create_listing(site, category)
                
                # Post to appropriate platform
                if site == 'craigslist':
                    url = self.post_to_craigslist(listing)
                elif site == 'facebook_marketplace':
                    url = self.post_to_facebook(listing)
                elif site == 'kijiji':
                    url = self.post_to_kijiji(listing)
                    
                if url:
                    # Track listing
                    self.listings['listings'].append({
                        'site': site,
                        'category': category,
                        'url': url,
                        'date': datetime.now().isoformat(),
                        'title': listing['title']
                    })
                    
                    # Update Asana
                    self._track_listing_in_asana(site, listing, url)
                    
                    # Save updated listings
                    self._save_listings()
                    
                # Wait between posts
                time.sleep(random.randint(300, 900))  # 5-15 minutes
                
    def _track_listing_in_asana(self, site: str, listing: Dict, url: str):
        """Track listing in Asana"""
        task_data = {
            'name': f"Listing: {listing['title']} ({site})",
            'notes': f"""
            Posted: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            Platform: {site}
            Category: {listing['category']}
            URL: {url}
            
            Content:
            {listing['description']}
            """,
            'custom_fields': {
                'listing_platform': site,
                'listing_url': url,
                'listing_status': 'active'
            }
        }
        
        self.asana.create_task(task_data)
        
    def schedule_daily_run(self):
        """Schedule daily listing creation"""
        # Run at different times each day to appear more natural
        run_hour = random.randint(9, 16)  # Between 9 AM and 4 PM
        run_minute = random.randint(0, 59)
        
        schedule.every().day.at(f"{run_hour:02d}:{run_minute:02d}").do(self.run_daily_listings)
        
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
