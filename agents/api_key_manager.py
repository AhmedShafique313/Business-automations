import os
import json
import logging
import asyncio
from typing import Dict, Optional
from playwright.async_api import async_playwright
from dataclasses import dataclass
from pathlib import Path

@dataclass
class APIKeyResult:
    success: bool
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    error: Optional[str] = None

class APIKeyManager:
    """Manages API key retrieval for various services"""
    
    def __init__(self, credentials_path: str = None, max_retries: int = 3, headless: bool = True):
        self.setup_logging()
        if credentials_path is None:
            credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials.json')
        self.credentials = self._load_credentials(credentials_path)
        self.credentials_path = credentials_path
        self.max_retries = max_retries
        self.headless = headless
        
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('api_keys.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('APIKeyManager')
        
    def _load_credentials(self, credentials_path: str) -> Dict:
        """Load credentials from file"""
        try:
            with open(credentials_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            return {}
            
    def _save_credentials(self):
        """Save updated credentials back to file"""
        try:
            with open(self.credentials_path, 'w') as f:
                json.dump(self.credentials, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving credentials: {str(e)}")

    async def _handle_2fa(self, page, platform: str):
        """Handle 2FA if needed"""
        try:
            # Wait for potential 2FA prompt
            two_fa_selector = 'text=Two-factor authentication, text=Security code, text=Verification code'
            two_fa_element = await page.wait_for_selector(two_fa_selector, timeout=5000)
            
            if two_fa_element:
                self.logger.info(f"2FA detected for {platform}. Waiting for manual input...")
                # Wait for manual 2FA completion
                await page.wait_for_navigation(timeout=300000)  # 5 minutes timeout
                return True
        except:
            # No 2FA prompt found
            pass
        return False
        
    async def _retry_with_backoff(self, func, platform: str):
        """Retry function with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                result = await func()
                if result.success:
                    return result
                    
                backoff = (2 ** attempt) * 1000  # Exponential backoff in ms
                self.logger.info(f"Attempt {attempt + 1} failed for {platform}. Retrying in {backoff/1000} seconds...")
                await asyncio.sleep(backoff/1000)
            except Exception as e:
                self.logger.error(f"Error in attempt {attempt + 1} for {platform}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return APIKeyResult(success=False, error=str(e))
                    
        return APIKeyResult(success=False, error=f"Failed after {self.max_retries} attempts")

    async def _setup_browser(self):
        """Setup browser with common configurations"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        )
        return playwright, browser, context

    async def _handle_google_login(self, page, context) -> bool:
        """Handle Google account login"""
        try:
            self.logger.info("Starting Google login process...")
            
            # Go to LinkedIn homepage first
            await page.goto('https://www.linkedin.com/', wait_until='domcontentloaded')
            await asyncio.sleep(5)
            
            # Click Sign In if on homepage
            try:
                signin = await page.wait_for_selector('a[data-tracking-control-name="guest_homepage-basic_sign-in-button"]', timeout=5000)
                if signin:
                    await signin.click()
                    await asyncio.sleep(3)
            except:
                self.logger.info("Already on login page")
            
            # Look for Google sign-in button
            try:
                google_button = await page.wait_for_selector('button.google-sign-in', timeout=10000)
                if google_button:
                    await google_button.click()
                    await asyncio.sleep(3)
                    
                    # Handle Google login popup
                    popup = context.pages[-1]
                    await popup.wait_for_load_state('domcontentloaded')
                    
                    # Enter email
                    self.logger.info("Entering Google email...")
                    await popup.fill('input[type="email"]', self.credentials['LINKEDIN']['email'])
                    await popup.keyboard.press('Enter')
                    await asyncio.sleep(3)
                    
                    # Enter password
                    self.logger.info("Entering Google password...")
                    await popup.fill('input[type="password"]', self.credentials['LINKEDIN']['password'])
                    await popup.keyboard.press('Enter')
                    await asyncio.sleep(5)
                    
                    # Wait for redirect back to LinkedIn
                    await page.wait_for_url('**/feed/**', timeout=30000)
                    return True
            except Exception as e:
                self.logger.error(f"Error during Google login: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in Google login process: {str(e)}")
            return False

    async def _wait_for_navigation(self, page, timeout=60000):
        """Helper function to wait for navigation with logging"""
        try:
            await page.wait_for_load_state('networkidle', timeout=timeout)
            await asyncio.sleep(3)  # Additional wait for stability
            return True
        except Exception as e:
            self.logger.error(f"Navigation timeout: {str(e)}")
            return False

    async def _check_login_state(self, page) -> bool:
        """Check if we're logged in to LinkedIn"""
        try:
            # Check for common LinkedIn logged-in elements
            profile_nav = await page.query_selector('nav[aria-label="primary"]')
            if profile_nav:
                self.logger.info("LinkedIn login successful - found primary navigation")
                return True

            # Check for feed URL
            current_url = page.url
            if 'linkedin.com/feed' in current_url:
                self.logger.info("LinkedIn login successful - on feed page")
                return True

            self.logger.warning("Not logged into LinkedIn")
            return False
        except Exception as e:
            self.logger.error(f"Error checking login state: {str(e)}")
            return False

    async def _try_linkedin_direct_login(self, page) -> bool:
        """Try logging in directly to LinkedIn"""
        try:
            self.logger.info("Attempting direct LinkedIn login...")
            
            # Fill username/email
            await page.fill('#username', self.credentials['LINKEDIN']['email'])
            await asyncio.sleep(1)
            
            # Fill password
            await page.fill('#password', self.credentials['LINKEDIN']['password'])
            await asyncio.sleep(1)
            
            # Click sign in
            await page.click('button[type="submit"]')
            await asyncio.sleep(5)
            
            # Check if login was successful
            return await self._check_login_state(page)
        except Exception as e:
            self.logger.error(f"Direct LinkedIn login failed: {str(e)}")
            return False

    async def get_linkedin_api_keys(self) -> APIKeyResult:
        """Get LinkedIn API keys through browser automation after manual login"""
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Go to LinkedIn login
                self.logger.info("Opening LinkedIn. Please login with Google...")
                await page.goto('https://www.linkedin.com/login')
                
                # Wait for user confirmation
                self.logger.info("Please type 'done' and press Enter once you've logged in:")
                user_input = input()
                
                if user_input.lower() != 'done':
                    return APIKeyResult(success=False, error="Login aborted")
                
                self.logger.info("Proceeding to developers page...")
                await page.goto('https://www.linkedin.com/developers/apps')
                await asyncio.sleep(5)
                
                # Log current state
                current_url = page.url
                self.logger.info(f"Current URL: {current_url}")
                
                # Try to create app
                create_button = await page.wait_for_selector('button:has-text("Create app")', timeout=10000)
                if create_button:
                    self.logger.info("Found create button, clicking...")
                    await create_button.click()
                    await asyncio.sleep(3)
                    
                    self.logger.info("Filling app details...")
                    await page.fill('input#name', 'Design Gaga App')
                    await page.fill('textarea#description', 'Design Gaga LinkedIn Integration')
                    await page.fill('input#companyName', 'Design Gaga')
                    
                    await page.check('input[type="checkbox"]')
                    await page.click('button:has-text("Create app")')
                    await asyncio.sleep(5)
                
                # Get app credentials
                app_card = await page.query_selector('.app-card')
                if app_card:
                    self.logger.info("Found app card, clicking...")
                    await app_card.click()
                    await asyncio.sleep(3)
                    
                    self.logger.info("Looking for Auth tab...")
                    await page.click('text=Auth')
                    await asyncio.sleep(3)
                    
                    client_id = await page.evaluate('document.querySelector("p:has-text(\\"Client ID\\") + p").textContent')
                    
                    show_button = await page.query_selector('text=Show')
                    if show_button:
                        await show_button.click()
                        await asyncio.sleep(1)
                        
                        client_secret = await page.evaluate('document.querySelector("p:has-text(\\"Client Secret\\") + p").textContent')
                        
                        if client_id and client_secret:
                            self.logger.info("Successfully retrieved API credentials!")
                            
                            if 'api_credentials' not in self.credentials['LINKEDIN']:
                                self.credentials['LINKEDIN']['api_credentials'] = {}
                            
                            self.credentials['LINKEDIN']['api_credentials'].update({
                                'client_id': client_id.strip(),
                                'client_secret': client_secret.strip()
                            })
                            self._save_credentials()
                            
                            return APIKeyResult(
                                success=True,
                                api_key=client_id.strip(),
                                api_secret=client_secret.strip()
                            )
                
                await context.close()
                return APIKeyResult(success=False, error="Could not retrieve app credentials")
                
            except Exception as e:
                self.logger.error(f"Error getting LinkedIn API keys: {str(e)}")
                return APIKeyResult(success=False, error=str(e))

    async def get_facebook_api_keys(self) -> APIKeyResult:
        """Get Facebook API keys through browser automation"""
        async with async_playwright() as p:
            try:
                # Launch browser with specific arguments
                browser = await p.chromium.launch(
                    headless=False,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
                
                # Create context with specific settings
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                )
                
                # Create page
                page = await context.new_page()
                page.set_default_timeout(60000)
                
                # Login
                await page.click('text=Log In')
                await page.fill('input[name="email"]', self.credentials['FACEBOOK']['email'])
                await page.fill('input[name="pass"]', self.credentials['FACEBOOK']['password'])
                await page.click('button[name="login"]')
                
                # Wait for navigation
                await page.wait_for_load_state('networkidle')
                
                # Handle 2FA if needed
                if await self._handle_2fa(page, 'Facebook'):
                    await page.wait_for_load_state('networkidle')
                
                # Go to Apps page
                await page.goto('https://developers.facebook.com/apps/')
                
                # Get first app or create new one
                app_id = None
                app_secret = None
                
                create_app_button = await page.query_selector('text=Create App')
                if create_app_button:
                    await create_app_button.click()
                    await page.click('text=Business')
                    await page.fill('input[name="name"]', 'Design Gaga App')
                    await page.click('text=Create App')
                    
                    # Get app credentials
                    await page.goto('https://developers.facebook.com/apps/')
                
                # Get app credentials
                app_element = await page.query_selector('.app-card')
                if app_element:
                    await app_element.click()
                    await page.goto(page.url + '/settings/basic/')
                    
                    app_id = await page.text_content('text=App ID >> xpath=following-sibling::*')
                    
                    # Show app secret
                    show_button = await page.query_selector('text=Show')
                    if show_button:
                        await show_button.click()
                        await asyncio.sleep(1)
                        
                        app_secret = await page.text_content('text=App Secret >> xpath=following-sibling::*')
                
                await browser.close()
                
                if app_id and app_secret:
                    # Update credentials
                    if 'api_credentials' not in self.credentials['FACEBOOK']:
                        self.credentials['FACEBOOK']['api_credentials'] = {}
                    
                    self.credentials['FACEBOOK']['api_credentials'].update({
                        'app_id': app_id.strip(),
                        'app_secret': app_secret.strip()
                    })
                    self._save_credentials()
                    
                    return APIKeyResult(
                        success=True,
                        api_key=app_id.strip(),
                        api_secret=app_secret.strip()
                    )
                else:
                    return APIKeyResult(
                        success=False,
                        error="Could not retrieve app credentials"
                    )
                    
            except Exception as e:
                self.logger.error(f"Error getting Facebook API keys: {str(e)}")
                return APIKeyResult(
                    success=False,
                    error=str(e)
                )
                
    async def get_instagram_api_keys(self) -> APIKeyResult:
        """Get Instagram API keys through Facebook Business Manager"""
        # Instagram API keys are managed through Facebook
        return await self.get_facebook_api_keys()
        
    async def get_pinterest_api_keys(self) -> APIKeyResult:
        """Get Pinterest API keys"""
        async with async_playwright() as p:
            try:
                playwright, browser, context = await self._setup_browser()
                page = await context.new_page()
                
                # Go to Pinterest Developers
                await page.goto('https://developers.pinterest.com/')
                
                # Login with Google
                await page.click('text=Sign in with Google')
                await page.fill('input[type="email"]', self.credentials['PINTEREST']['email'])
                await page.click('text=Next')
                await page.fill('input[type="password"]', self.credentials['PINTEREST']['password'])
                await page.click('text=Next')
                
                # Wait for navigation
                await page.wait_for_load_state('networkidle')
                
                # Handle 2FA if needed
                if await self._handle_2fa(page, 'Pinterest'):
                    await page.wait_for_load_state('networkidle')
                
                # Go to Apps page
                await page.goto('https://developers.pinterest.com/apps/')
                
                # Get first app or create new one
                create_app_button = await page.query_selector('text=Create app')
                if create_app_button:
                    await create_app_button.click()
                    await page.fill('input[name="name"]', 'Design Gaga App')
                    await page.fill('input[name="description"]', 'Design Gaga Pinterest Integration')
                    await page.click('text=Create')
                
                # Get app credentials
                app_element = await page.query_selector('.app-card')
                if app_element:
                    await app_element.click()
                    
                    app_id = await page.text_content('text=App ID >> xpath=following-sibling::*')
                    app_secret = await page.text_content('text=App secret >> xpath=following-sibling::*')
                    
                    if app_id and app_secret:
                        # Update credentials
                        if 'api_credentials' not in self.credentials['PINTEREST']:
                            self.credentials['PINTEREST']['api_credentials'] = {}
                        
                        self.credentials['PINTEREST']['api_credentials'].update({
                            'app_id': app_id.strip(),
                            'app_secret': app_secret.strip()
                        })
                        self._save_credentials()
                        
                        return APIKeyResult(
                            success=True,
                            api_key=app_id.strip(),
                            api_secret=app_secret.strip()
                        )
                
                return APIKeyResult(
                    success=False,
                    error="Could not retrieve app credentials"
                )
                
            except Exception as e:
                self.logger.error(f"Error getting Pinterest API keys: {str(e)}")
                return APIKeyResult(
                    success=False,
                    error=str(e)
                )

async def main():
    """Main function to run API key retrieval"""
    api_manager = APIKeyManager(headless=False)
    
    # Get LinkedIn API keys
    print("\nAttempting to get LinkedIn API keys...")
    result = await api_manager.get_linkedin_api_keys()
    
    if result.success:
        print("LinkedIn API keys retrieved successfully!")
        print(f"API Key: {result.api_key[:5]}...")
        print(f"API Secret: {result.api_secret[:5]}...")
    else:
        print(f"Error getting LinkedIn API keys: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())
