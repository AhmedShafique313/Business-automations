"""Business generation module for Design Gaga automation system.

This module handles the core business generation functionality, including:
- Real estate listing discovery
- Agent outreach
- Cold calling
- Email follow-ups
- Web automation
- Social media integration
"""

import os
import json
import time
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
from pythonjsonlogger import jsonlogger
from config_manager import ConfigManager

# Optional dependencies that will be imported only if needed
OPTIONAL_DEPS = {
    'twilio': {'imported': False, 'module': None},
    'google': {'imported': False, 'module': None},
    'selenium': {'imported': False, 'module': None},
    'speech': {'imported': False, 'module': None}
}

class BusinessGenerator:
    """Business generator for automating various business tasks.
    
    This class handles various business automation tasks including:
    - Finding real estate listings
    - Identifying potential agents
    - Making cold calls
    - Sending follow-up emails
    - Managing social media presence
    
    The class supports optional features that can be enabled/disabled
    through configuration.
    """
    
    def __init__(self):
        """Initialize the business generator with company details and credentials."""
        self.config = ConfigManager()
        self.setup_logging()
        self.load_company_details()
        self.init_optional_features()
        
    def setup_logging(self):
        """Setup JSON logging with detailed error tracking."""
        try:
            log_config = self.config.get('logging', default={})
            log_path = Path(self.config.get('paths', 'logs', default='logs'))
            log_path.mkdir(exist_ok=True)
            
            # Set up file handler
            file_handler = logging.FileHandler(
                log_path / 'business_generator.log'
            )
            file_handler.setFormatter(jsonlogger.JsonFormatter(
                log_config.get('format', '%(asctime)s %(name)s %(levelname)s %(message)s'),
                timestamp=True
            ))
            
            # Set up console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(jsonlogger.JsonFormatter(
                log_config.get('format', '%(asctime)s %(name)s %(levelname)s %(message)s'),
                timestamp=True
            ))
            
            # Configure logger
            self.logger = logging.getLogger('BusinessGenerator')
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(log_config.get('level', 'INFO'))
            
        except Exception as e:
            # Fallback to basic logging if JSON logging fails
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger('BusinessGenerator')
            self.logger.error(f"Error setting up JSON logging: {str(e)}")

    def load_company_details(self):
        """Load company details from configuration."""
        try:
            self.company_name = self.config.get('company', 'name')
            self.website = self.config.get('company', 'website')
            self.phone = self.config.get('company', 'phone')
            self.business_type = self.config.get('company', 'business_type')
            self.location = self.config.get('company', 'location')
            
            if not all([self.company_name, self.website, self.business_type, self.location]):
                self.logger.warning("Some company details are missing")
            
            # Load templates
            self.templates = self._load_conversation_templates()
            
        except Exception as e:
            self.logger.error(f"Error loading company details: {str(e)}")
            raise RuntimeError("Failed to load essential company details")

    def init_optional_features(self):
        """Initialize optional features based on configuration."""
        features = self.config.get('features', default={})
        
        # Initialize each feature if enabled
        for feature, config in features.items():
            if config.get('enabled', False):
                self.logger.info(f"Initializing feature: {feature}")
                try:
                    if feature == 'voice_commands':
                        self._init_voice_feature()
                    elif feature == 'google_integration':
                        self._init_google_feature()
                    elif feature == 'web_automation':
                        self._init_web_automation()
                    elif feature == 'email_outreach':
                        self._init_email_feature()
                except Exception as e:
                    self.logger.error(f"Failed to initialize {feature}: {str(e)}")
                    
    def _init_voice_feature(self):
        """Initialize voice command feature."""
        if self._check_twilio_available() and self._check_speech_available():
            self.setup_twilio()
            self.setup_speech()
        else:
            self.logger.warning("Voice commands disabled due to missing dependencies")
            
    def _init_google_feature(self):
        """Initialize Google API integration."""
        if self._check_google_available():
            self.setup_google_api()
        else:
            self.logger.warning("Google integration disabled due to missing dependencies")
            
    def _init_web_automation(self):
        """Initialize web automation feature."""
        if self._check_selenium_available():
            self.setup_selenium()
        else:
            self.logger.warning("Web automation disabled due to missing dependencies")
            
    def _init_email_feature(self):
        """Initialize email outreach feature."""
        # Email feature uses built-in modules, so just verify config
        email_config = self.config.get('features', 'email_outreach', default={})
        if not email_config.get('max_daily'):
            self.logger.warning("Email outreach limits not configured")
            
    def _check_twilio_available(self) -> bool:
        """Check if Twilio is available and configured."""
        if OPTIONAL_DEPS['twilio']['imported']:
            return True
            
        try:
            import twilio.rest
            OPTIONAL_DEPS['twilio']['module'] = twilio.rest
            OPTIONAL_DEPS['twilio']['imported'] = True
            
            # Verify credentials
            twilio_config = self.config.get('api', 'twilio', default={})
            if not all([
                twilio_config.get('account_sid'),
                twilio_config.get('auth_token'),
                twilio_config.get('phone_number')
            ]):
                self.logger.warning("Twilio credentials missing")
                return False
                
            return True
            
        except ImportError:
            self.logger.warning("Twilio package not available")
            return False
            
    def _check_google_available(self) -> bool:
        """Check if Google API is available and configured."""
        if OPTIONAL_DEPS['google']['imported']:
            return True
            
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            OPTIONAL_DEPS['google']['module'] = {
                'credentials': Credentials,
                'request': Request,
                'flow': InstalledAppFlow
            }
            OPTIONAL_DEPS['google']['imported'] = True
            
            # Verify credentials
            google_config = self.config.get('api', 'google', default={})
            creds_path = Path(google_config.get('credentials_file', ''))
            if not creds_path.exists():
                self.logger.warning("Google credentials file missing")
                return False
                
            return True
            
        except ImportError:
            self.logger.warning("Google API packages not available")
            return False
            
    def _check_selenium_available(self) -> bool:
        """Check if Selenium is available and configured."""
        if OPTIONAL_DEPS['selenium']['imported']:
            return True
            
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            OPTIONAL_DEPS['selenium']['module'] = {
                'webdriver': webdriver,
                'options': Options
            }
            OPTIONAL_DEPS['selenium']['imported'] = True
            return True
            
        except ImportError:
            self.logger.warning("Selenium not available")
            return False
            
    def _check_speech_available(self) -> bool:
        """Check if speech recognition is available."""
        if OPTIONAL_DEPS['speech']['imported']:
            return True
            
        try:
            import speech_recognition
            import pyttsx3
            
            OPTIONAL_DEPS['speech']['module'] = {
                'recognizer': speech_recognition,
                'engine': pyttsx3
            }
            OPTIONAL_DEPS['speech']['imported'] = True
            return True
            
        except ImportError:
            self.logger.warning("Speech recognition packages not available")
            return False

    def setup_twilio(self):
        """Setup Twilio client if credentials are available."""
        try:
            twilio_config = self.config.get('api', 'twilio', default={})
            self.twilio_client = OPTIONAL_DEPS['twilio']['module'].Client(
                twilio_config['account_sid'],
                twilio_config['auth_token']
            )
            self.logger.info("Twilio client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Twilio: {str(e)}")

    def setup_google_api(self):
        """Setup Google API client if credentials are available."""
        try:
            google_config = self.config.get('api', 'google', default={})
            creds_path = Path(google_config.get('credentials_file', ''))
            creds_data = json.load(open(creds_path))
            credentials = OPTIONAL_DEPS['google']['module']['credentials'].from_authorized_user_info(creds_data)
            self.gmb_service = OPTIONAL_DEPS['google']['module']['credentials'].build('mybusiness', 'v4', credentials=credentials)
            self.logger.info("Google API client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google API: {str(e)}")

    def setup_selenium(self):
        """Setup Selenium WebDriver if available."""
        try:
            options = OPTIONAL_DEPS['selenium']['module']['options'].Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            self.driver = OPTIONAL_DEPS['selenium']['module']['webdriver'].Chrome(options=options)
            self.logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Selenium: {str(e)}")

    def setup_speech(self):
        """Setup speech recognition and synthesis if available."""
        try:
            self.speech_recognizer = OPTIONAL_DEPS['speech']['module']['recognizer'].Recognizer()
            self.speech_engine = OPTIONAL_DEPS['speech']['module']['engine'].init()
            self.logger.info("Speech components initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize speech components: {str(e)}")

    def _load_conversation_templates(self) -> Dict:
        """Load conversation templates with fallback to defaults."""
        try:
            template_path = Path('templates/conversation_templates.json')
            if not template_path.exists():
                self.logger.warning("Template file not found, creating default templates")
                self._create_default_templates()
            
            with open(template_path) as f:
                templates = json.load(f)
            return templates.get(self.business_type, templates['default'])
        except Exception as e:
            self.logger.error(f"Error loading templates: {str(e)}")
            return self._get_default_templates()

    def _create_default_templates(self):
        """Create default templates if they don't exist."""
        default_templates = self._get_default_templates()
        os.makedirs('templates', exist_ok=True)
        
        with open('templates/conversation_templates.json', 'w') as f:
            json.dump({'default': default_templates}, f, indent=2)

    def _get_default_templates(self) -> Dict:
        """Get default templates for basic functionality."""
        return {
            'email': {
                'subject': 'Introducing {company_name}',
                'body': 'Hello {name},\n\nI hope this email finds you well...'
            },
            'call': {
                'greeting': 'Hello, this is {agent_name} from {company_name}',
                'pitch': 'We specialize in...'
            },
            'message': {
                'intro': 'Hi {name}, this is {company_name}',
                'follow_up': 'Would you like to learn more?'
            }
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    @sleep_and_retry
    @limits(calls=30, period=60)
    def find_real_estate_listings(self) -> List[Dict]:
        """Find real estate listings with rate limiting and retries."""
        try:
            if not OPTIONAL_DEPS['selenium']['imported']:
                return []
                
            listings = []
            # Implementation here...
            return listings
        except Exception as e:
            self.logger.error(f"Error finding listings: {str(e)}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def find_real_estate_agents(self) -> List[Dict]:
        """Find real estate agents with retry logic."""
        try:
            agents = []
            # Implementation here...
            return agents
        except Exception as e:
            self.logger.error(f"Error finding agents: {str(e)}")
            return []

    def generate_target_list(self) -> List[Dict]:
        """Generate list of potential customers based on business type and location."""
        try:
            targets = []
            
            # Scrape local business directories
            directories = [
                'yellowpages.com',
                'yelp.com',
                'google.com/maps',
                'linkedin.com/company'
            ]
            
            for directory in directories:
                self.logger.info(f"Scraping {directory} for potential customers...")
                
                # Configure selenium webdriver
                options = OPTIONAL_DEPS['selenium']['module']['options'].Options()
                options.add_argument('--headless')
                driver = OPTIONAL_DEPS['selenium']['module']['webdriver'].Chrome(options=options)
                
                try:
                    # Search for relevant businesses
                    search_url = f"https://www.{directory}/search?q={self.business_type}&l={self.location}"
                    driver.get(search_url)
                    
                    # Wait for results to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "business-name"))
                    )
                    
                    # Extract business information
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    businesses = soup.find_all(class_="business-name")
                    
                    for business in businesses:
                        contact_info = {
                            'name': business.text.strip(),
                            'website': business.find('a')['href'] if business.find('a') else None,
                            'phone': self._extract_phone(business),
                            'email': self._extract_email(business),
                            'source': directory
                        }
                        targets.append(contact_info)
                
                finally:
                    driver.quit()
            
            # Deduplicate and validate contacts
            targets = self._validate_contacts(targets)
            
            return targets
            
        except Exception as e:
            self.logger.error(f"Error generating target list: {str(e)}")
            return []

    def _extract_phone(self, element) -> str:
        """Extract and validate phone numbers from HTML elements."""
        try:
            phone_element = element.find(class_="phone")
            if phone_element:
                phone = phone_element.text.strip()
                parsed = phonenumbers.parse(phone, "US")
                if phonenumbers.is_valid_number(parsed):
                    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except Exception as e:
            self.logger.debug(f"Error extracting phone: {str(e)}")
        return None

    def _extract_email(self, element) -> str:
        """Extract email addresses from HTML elements."""
        try:
            email_element = element.find(class_="email")
            if email_element:
                return email_element.text.strip()
        except Exception as e:
            self.logger.debug(f"Error extracting email: {str(e)}")
        return None

    def _validate_contacts(self, contacts: List[Dict]) -> List[Dict]:
        """Deduplicate and validate contact information."""
        validated = []
        seen = set()
        
        for contact in contacts:
            # Create unique identifier
            identifier = f"{contact['name']}_{contact['phone']}"
            
            if identifier not in seen and (contact['phone'] or contact['email']):
                seen.add(identifier)
                validated.append(contact)
        
        return validated

    def make_cold_call(self, contact: Dict) -> bool:
        """Make an AI-powered cold call using natural conversation."""
        try:
            # Get conversation template
            template = self.templates['cold_call']
            
            # Initialize call
            call = self.twilio_client.calls.create(
                to=contact['phone'],
                from_=self.phone,
                url='http://your-twilio-webhook.com/voice'  # Webhook to handle call flow
            )
            
            # Monitor call status
            while call.status != 'completed':
                time.sleep(1)
                call = self.twilio_client.calls(call.sid).fetch()
            
            return call.status == 'completed'
            
        except Exception as e:
            self.logger.error(f"Error making cold call to {contact['name']}: {str(e)}")
            return False

    def handle_call_webhook(self, request):
        """Handle incoming webhook requests for call flow."""
        response = VoiceResponse()
        
        # Get conversation template
        template = self.templates['cold_call']
        
        # Initial greeting
        response.say(template['greeting'])
        
        # Gather customer response
        gather = Gather(input='speech', timeout=3)
        gather.say(template['pitch'])
        response.append(gather)
        
        # Handle no input
        response.say(template['no_response'])
        
        return str(response)

    def optimize_gmb(self):
        """Optimize Google My Business listing."""
        try:
            # Get account and location
            accounts = self.gmb_service.accounts().list().execute()
            account = accounts['accounts'][0]  # Assuming first account
            
            locations = self.gmb_service.accounts().locations().list(
                parent=account['name']
            ).execute()
            
            if 'locations' in locations:
                location = locations['locations'][0]  # Assuming first location
                
                # Update business information
                location_data = {
                    'title': self.company_name,
                    'websiteUrl': self.website,
                    'primaryPhone': self.phone,
                    'serviceArea': {
                        'businessType': 'CUSTOMER_AND_BUSINESS_LOCATION',
                        'places': [{
                            'name': self.location
                        }]
                    }
                }
                
                # Update GMB listing
                self.gmb_service.accounts().locations().patch(
                    name=location['name'],
                    body=location_data,
                    updateMask='title,websiteUrl,primaryPhone,serviceArea'
                ).execute()
                
                # Post updates and photos regularly
                self._post_gmb_updates(location['name'])
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error optimizing GMB: {str(e)}")
            return False

    def _post_gmb_updates(self, location_name: str):
        """Post regular updates to Google My Business."""
        try:
            # Generate update content
            update = {
                'topicType': 'STANDARD',
                'languageCode': 'en-US',
                'summary': f"Check out our latest services at {self.company_name}!",
                'callToAction': {
                    'actionType': 'LEARN_MORE',
                    'url': self.website
                }
            }
            
            # Post update
            self.gmb_service.accounts().locations().localPosts().create(
                parent=location_name,
                body=update
            ).execute()
            
        except Exception as e:
            self.logger.error(f"Error posting GMB update: {str(e)}")

    def send_follow_up_email(self, contact: Dict) -> bool:
        """Send personalized follow-up email."""
        try:
            # Get email template
            template = self.templates['follow_up_email']
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.get('smtp', 'user')
            msg['To'] = contact['email']
            msg['Subject'] = template['subject'].format(
                company_name=contact['name']
            )
            
            # Add personalized body
            body = template['body'].format(
                contact_name=contact['name'],
                company_name=self.company_name,
                website=self.website,
                phone=self.phone
            )
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.get('smtp', 'server')) as server:
                server.starttls()
                server.login(self.config.get('smtp', 'user'), self.config.get('smtp', 'password'))
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending follow-up email to {contact['name']}: {str(e)}")
            return False

    def generate_business(self):
        """Main business generation loop."""
        while True:
            try:
                # Generate new target list
                targets = self.generate_target_list()
                self.logger.info(f"Generated {len(targets)} potential targets")
                
                # Process each target
                for contact in targets:
                    # Make cold call
                    if contact['phone']:
                        call_success = self.make_cold_call(contact)
                        if call_success:
                            self.logger.info(f"Successfully called {contact['name']}")
                    
                    # Send follow-up email
                    if contact['email']:
                        email_success = self.send_follow_up_email(contact)
                        if email_success:
                            self.logger.info(f"Successfully emailed {contact['name']}")
                    
                    # Pause between contacts
                    time.sleep(random.randint(30, 60))
                
                # Optimize GMB listing
                self.optimize_gmb()
                
                # Wait before next batch
                time.sleep(3600)  # 1 hour
                
            except Exception as e:
                self.logger.error(f"Error in business generation loop: {str(e)}")
                time.sleep(300)  # 5 minutes
                continue

if __name__ == "__main__":
    generator = BusinessGenerator()
    generator.generate_business()
