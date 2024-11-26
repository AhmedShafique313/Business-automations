import os
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import schedule
import time
from datetime import datetime, timedelta
import json
import re
from keyring import get_password, set_password
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import yake
import spacy
from googleapiclient.discovery import build
from asana_tracker import AsanaTracker

class SEOAgent:
    def __init__(self, work_dir: str):
        self.work_dir = work_dir
        self.asana = AsanaTracker(os.getenv('ASANA_WORKSPACE_GID'))
        self.driver = self._setup_webdriver()
        
        # Load credentials securely
        self._setup_credentials()
        
        # Initialize NLP
        self.nlp = spacy.load('en_core_web_lg')
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize keyword extractor
        self.keyword_extractor = yake.KeywordExtractor(
            lan="en",
            n=3,  # ngram size
            dedupLim=0.3,
            top=20,
            features=None
        )
        
    def _setup_webdriver(self) -> webdriver.Chrome:
        """Setup Chrome webdriver with proper options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=options)
        
    def _setup_credentials(self):
        """Setup secure credential storage"""
        # Store credentials in system keyring
        if not get_password('siteground', 'vandan@getfoolish.com'):
            set_password('siteground', 'vandan@getfoolish.com', 'W1z@rdJungle')
            
    def _load_config(self) -> Dict:
        """Load SEO configuration"""
        config_path = os.path.join(self.work_dir, 'config', 'seo_config.json')
        with open(config_path) as f:
            return json.load(f)
            
    def login_to_siteground(self):
        """Login to Siteground securely"""
        try:
            self.driver.get('https://login.siteground.com/login')
            
            # Wait for login form
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'email'))
            )
            
            # Get credentials securely
            username = 'vandan@getfoolish.com'
            password = get_password('siteground', username)
            
            # Login
            username_field.send_keys(username)
            self.driver.find_element(By.NAME, 'password').send_keys(password)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            
            # Wait for dashboard
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'dashboard'))
            )
            
            return True
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False
            
    def analyze_site(self) -> Dict:
        """Analyze website content and performance"""
        results = {
            'pages': [],
            'issues': [],
            'keywords': {},
            'performance': {}
        }
        
        try:
            # Get sitemap
            sitemap_url = urljoin(self.config['base_url'], 'sitemap.xml')
            response = requests.get(sitemap_url)
            root = ET.fromstring(response.content)
            
            # Analyze each page
            for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                page_url = url.text
                results['pages'].append(self.analyze_page(page_url))
                
            # Aggregate results
            self._aggregate_results(results)
            
            # Track in Asana
            self._track_analysis(results)
            
            return results
            
        except Exception as e:
            print(f"Site analysis failed: {str(e)}")
            return results
            
    def analyze_page(self, url: str) -> Dict:
        """Analyze a single page"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            text_content = ' '.join([p.text for p in soup.find_all('p')])
            
            # Analyze with spaCy
            doc = self.nlp(text_content)
            
            # Extract keywords
            keywords = self.keyword_extractor.extract_keywords(text_content)
            
            # Check meta tags
            meta_title = soup.find('title')
            meta_description = soup.find('meta', {'name': 'description'})
            
            # Check headings
            headings = {
                f'h{i}': len(soup.find_all(f'h{i}'))
                for i in range(1, 7)
            }
            
            # Check images
            images = [
                {
                    'src': img.get('src', ''),
                    'alt': img.get('alt', ''),
                    'issues': self._check_image_issues(img)
                }
                for img in soup.find_all('img')
            ]
            
            return {
                'url': url,
                'title': meta_title.text if meta_title else None,
                'description': meta_description['content'] if meta_description else None,
                'keywords': keywords,
                'headings': headings,
                'images': images,
                'word_count': len(doc),
                'readability_score': self._calculate_readability(text_content),
                'issues': self._check_page_issues(soup)
            }
            
        except Exception as e:
            print(f"Page analysis failed for {url}: {str(e)}")
            return {'url': url, 'error': str(e)}
            
    def optimize_site(self):
        """Optimize website based on analysis"""
        try:
            # Analyze current state
            analysis = self.analyze_site()
            
            # Login to Siteground
            if not self.login_to_siteground():
                raise Exception("Failed to login to Siteground")
                
            # Optimize each page
            for page in analysis['pages']:
                self.optimize_page(page)
                
            # Generate optimization report
            report = self._generate_report(analysis)
            
            # Track in Asana
            self._track_optimization(report)
            
            return report
            
        except Exception as e:
            print(f"Site optimization failed: {str(e)}")
            return None
            
    def optimize_page(self, page_data: Dict):
        """Optimize a single page"""
        try:
            # Navigate to page editor
            page_url = page_data['url']
            edit_url = self._get_edit_url(page_url)
            self.driver.get(edit_url)
            
            # Wait for editor
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'content'))
            )
            
            # Optimize meta tags
            if not page_data.get('title'):
                self._update_meta_title(page_data)
            if not page_data.get('description'):
                self._update_meta_description(page_data)
                
            # Optimize headings
            if page_data['headings'].get('h1', 0) != 1:
                self._fix_headings(page_data)
                
            # Optimize images
            for image in page_data['images']:
                if image['issues']:
                    self._fix_image(image)
                    
            # Add schema markup
            self._add_schema_markup(page_data)
            
            # Save changes
            self.driver.find_element(By.ID, 'publish').click()
            time.sleep(2)
            
        except Exception as e:
            print(f"Page optimization failed for {page_data['url']}: {str(e)}")
            
    def generate_content_suggestions(self, page_data: Dict) -> List[Dict]:
        """Generate content improvement suggestions"""
        suggestions = []
        
        # Analyze competitors
        competitor_data = self._analyze_competitors(page_data['keywords'])
        
        # Generate topic suggestions
        topics = self._generate_topics(page_data, competitor_data)
        
        for topic in topics:
            suggestions.append({
                'topic': topic['title'],
                'keywords': topic['keywords'],
                'content_outline': self._generate_outline(topic),
                'estimated_impact': self._estimate_impact(topic)
            })
            
        return suggestions
        
    def monitor_rankings(self):
        """Monitor search rankings for target keywords"""
        try:
            service = build('customsearch', 'v1', developerKey=os.getenv('GOOGLE_API_KEY'))
            
            results = {}
            for keyword in self.config['target_keywords']:
                res = service.cse().list(
                    q=keyword,
                    cx=os.getenv('GOOGLE_CSE_ID')
                ).execute()
                
                # Find our position
                position = None
                for i, item in enumerate(res['items']):
                    if self.config['base_url'] in item['link']:
                        position = i + 1
                        break
                        
                results[keyword] = {
                    'position': position,
                    'date': datetime.now().isoformat()
                }
                
            # Save results
            self._save_rankings(results)
            
            # Track in Asana
            self._track_rankings(results)
            
            return results
            
        except Exception as e:
            print(f"Ranking monitoring failed: {str(e)}")
            return None
            
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score"""
        # Implement Flesch-Kincaid or similar
        pass
        
    def _check_page_issues(self, soup: BeautifulSoup) -> List[Dict]:
        """Check for common SEO issues"""
        issues = []
        
        # Check title length
        title = soup.find('title')
        if title and (len(title.text) < 30 or len(title.text) > 60):
            issues.append({
                'type': 'title_length',
                'message': 'Title should be between 30-60 characters'
            })
            
        # Check meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if not meta_desc or len(meta_desc['content']) < 120:
            issues.append({
                'type': 'meta_description',
                'message': 'Meta description missing or too short'
            })
            
        # Check heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if len(soup.find_all('h1')) != 1:
            issues.append({
                'type': 'h1_tag',
                'message': 'Page should have exactly one H1 tag'
            })
            
        return issues
        
    def _check_image_issues(self, img) -> List[Dict]:
        """Check for image optimization issues"""
        issues = []
        
        if not img.get('alt'):
            issues.append({
                'type': 'missing_alt',
                'message': 'Image missing alt text'
            })
            
        if not img.get('loading') == 'lazy':
            issues.append({
                'type': 'no_lazy_loading',
                'message': 'Image not using lazy loading'
            })
            
        return issues
        
    def _track_analysis(self, results: Dict):
        """Track analysis results in Asana"""
        task_data = {
            'name': f"SEO Analysis - {datetime.now().strftime('%Y-%m-%d')}",
            'notes': self._format_analysis_notes(results),
            'custom_fields': {
                'analysis_type': 'seo',
                'total_issues': len(results['issues']),
                'priority_issues': len([i for i in results['issues'] if i['severity'] == 'high'])
            }
        }
        
        self.asana.create_task(task_data)
        
    def _track_optimization(self, report: Dict):
        """Track optimization in Asana"""
        task_data = {
            'name': f"SEO Optimization - {datetime.now().strftime('%Y-%m-%d')}",
            'notes': self._format_optimization_notes(report),
            'custom_fields': {
                'optimization_type': 'seo',
                'changes_made': len(report['changes']),
                'estimated_impact': report['estimated_impact']
            }
        }
        
        self.asana.create_task(task_data)
        
    def _track_rankings(self, results: Dict):
        """Track ranking changes in Asana"""
        task_data = {
            'name': f"SEO Rankings - {datetime.now().strftime('%Y-%m-%d')}",
            'notes': self._format_ranking_notes(results),
            'custom_fields': {
                'tracking_type': 'rankings',
                'improved_keywords': len([k for k in results if results[k]['change'] > 0]),
                'declined_keywords': len([k for k in results if results[k]['change'] < 0])
            }
        }
        
        self.asana.create_task(task_data)
        
    def schedule_daily_tasks(self):
        """Schedule daily SEO tasks"""
        # Analyze site daily
        schedule.every().day.at("01:00").do(self.analyze_site)
        
        # Monitor rankings daily
        schedule.every().day.at("02:00").do(self.monitor_rankings)
        
        # Optimize weekly
        schedule.every().monday.at("03:00").do(self.optimize_site)
        
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
