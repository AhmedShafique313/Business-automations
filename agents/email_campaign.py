import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
from mailjet_rest import Client
from communication_tracker import CommunicationTracker
import aiosqlite
import os

class EmailRateLimiter:
    def __init__(self, db_path: str = 'agents/email_limiter.db'):
        """Initialize email rate limiter with SQLite database"""
        self.db_path = db_path
        self.daily_limit = 200
        self._ensure_db()

    async def _ensure_db(self):
        """Ensure database and tables exist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS email_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()

    async def can_send_email(self, email: str) -> bool:
        """Check if we can send an email based on daily limits"""
        today = datetime.now().date()
        async with aiosqlite.connect(self.db_path) as db:
            # Count emails sent today
            cursor = await db.execute('''
                SELECT COUNT(*) FROM email_logs 
                WHERE date(sent_at) = date(?)
            ''', (today.isoformat(),))
            count = await cursor.fetchone()
            return count[0] < self.daily_limit

    async def log_email_sent(self, email: str):
        """Log an email being sent"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT INTO email_logs (email) VALUES (?)',
                (email,)
            )
            await db.commit()

    async def get_remaining_quota(self) -> int:
        """Get remaining email quota for today"""
        today = datetime.now().date()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT COUNT(*) FROM email_logs 
                WHERE date(sent_at) = date(?)
            ''', (today.isoformat(),))
            count = await cursor.fetchone()
            return self.daily_limit - count[0]

class EmailCampaign:
    def __init__(self, credentials_path: str = 'agents/credentials.json'):
        """Initialize Email Campaign Manager with Mailjet"""
        self.setup_logging()
        self.credentials = self._load_credentials(credentials_path)
        self.mailjet = Client(
            auth=(self.credentials['api_key'], self.credentials['api_secret']),
            version='v3.1'
        )
        self.campaign_data_path = Path('agents/campaign_data')
        self.campaign_data_path.mkdir(exist_ok=True)
        self.tracker = CommunicationTracker(credentials_path)
        self.rate_limiter = EmailRateLimiter()

    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('email_campaign.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('EmailCampaign')

    def _load_credentials(self, credentials_path: str) -> Dict:
        """Load Mailjet credentials from file"""
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                return creds['MAILJET']
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            raise

    async def send_campaign_email(self, contact: Dict, message_data: Dict) -> bool:
        """Send a campaign email to a contact"""
        # Check if we can send more emails today
        if not await self.rate_limiter.can_send_email(contact['email']):
            remaining = await self.rate_limiter.get_remaining_quota()
            self.logger.warning(f"⚠️ Daily email limit reached. Remaining quota: {remaining}")
            return False

        data = {
            'Messages': [
                {
                    'From': {
                        'Email': self.credentials['from_email'],
                        'Name': f"{self.credentials['sender_name']}, {self.credentials['sender_title']}"
                    },
                    'To': [
                        {
                            'Email': contact['email'],
                            'Name': contact['name']
                        }
                    ],
                    'Subject': message_data['subject'].format(**contact),
                    'HTMLPart': message_data['html_content'].format(**contact),
                    'CustomID': f"design_gaga_campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            ]
        }

        try:
            result = self.mailjet.send.create(data=data)
            
            if result.status_code == 200:
                # Log the sent email
                await self.rate_limiter.log_email_sent(contact['email'])
                
                self.logger.info(f"✅ Email sent to {contact['email']}")
                # Track the email in Asana
                await self.tracker.track_email_message(contact, message_data, 'Sent')
                
                # Log remaining quota
                remaining = await self.rate_limiter.get_remaining_quota()
                self.logger.info(f"📊 Remaining email quota for today: {remaining}")
                
                return True
            else:
                self.logger.error(f"❌ Error sending email to {contact['email']}:")
                self.logger.error(result.json())
                # Track the failed email
                await self.tracker.track_email_message(contact, message_data, 'Failed')
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error: {str(e)}")
            # Track the error
            await self.tracker.track_email_message(contact, message_data, f'Error: {str(e)}')
            return False

    async def run_campaign_step(self, campaign_id: str) -> None:
        """Run one step of the campaign"""
        campaign_file = self.campaign_data_path / f"{campaign_id}.json"
        
        if not campaign_file.exists():
            self.logger.error(f"Campaign {campaign_id} not found")
            return
            
        with open(campaign_file, 'r') as f:
            campaign_data = json.load(f)
            
        remaining_quota = await self.rate_limiter.get_remaining_quota()
        if remaining_quota <= 0:
            self.logger.warning("⚠️ Daily email quota exhausted. Waiting for next day.")
            return
            
        self.logger.info(f"📊 Starting campaign step with {remaining_quota} emails remaining for today")
        
        for contact in campaign_data['target_list']:
            progress = campaign_data['progress'].get(contact['email'], {
                'current_step': 0,
                'last_message': None
            })
            
            if progress['current_step'] >= len(campaign_data['message_sequence']):
                continue
                
            message_data = campaign_data['message_sequence'][progress['current_step']]
            
            # Check if enough time has passed since last message
            if progress['last_message']:
                last_message_time = datetime.fromisoformat(progress['last_message'])
                if datetime.now() - last_message_time < timedelta(hours=message_data.get('delay_hours', 0)):
                    continue
            
            # Check remaining quota before sending
            if await self.rate_limiter.get_remaining_quota() <= 0:
                self.logger.warning("⚠️ Daily email quota reached during campaign. Stopping for today.")
                break
                
            if await self.send_campaign_email(contact, message_data):
                progress['current_step'] += 1
                progress['last_message'] = datetime.now().isoformat()
                campaign_data['progress'][contact['email']] = progress
                
                # Save progress after each successful send
                with open(campaign_file, 'w') as f:
                    json.dump(campaign_data, f, indent=2)
            else:
                # If send failed, stop the campaign for today
                self.logger.warning("⚠️ Email send failed. Stopping campaign for today.")
                break

    async def get_campaign_stats(self) -> Dict:
        """Get current campaign statistics"""
        remaining_quota = await self.rate_limiter.get_remaining_quota()
        return {
            'remaining_daily_quota': remaining_quota,
            'total_daily_limit': self.rate_limiter.daily_limit,
            'emails_sent_today': self.rate_limiter.daily_limit - remaining_quota
        }

    def create_campaign(self, name: str, message_sequence: List[Dict], target_list: List[Dict]) -> str:
        """Create a new email campaign"""
        campaign_id = f"{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        campaign_data = {
            'id': campaign_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'message_sequence': message_sequence,
            'target_list': target_list,
            'progress': {contact['email']: {'current_step': 0, 'last_message': None} 
                        for contact in target_list}
        }
        
        # Save campaign data
        with open(self.campaign_data_path / f"{campaign_id}.json", 'w') as f:
            json.dump(campaign_data, f, indent=2)
            
        self.logger.info(f"Created campaign: {campaign_id}")
        return campaign_id

async def main():
    campaign = EmailCampaign()
    
    # Example message sequence
    message_sequence = [
        {
            'subject': "Enhance Your {location} Listings with Professional Home Staging",
            'html_content': """
                <html>
                <body>
                <p>Hello {name},</p>
                
                <p>I'm Gagan from Design Gaga, and I noticed your impressive listings in {location}. 
                We specialize in luxury home staging and have helped properties sell 60% faster.</p>
                
                <p>Would you be interested in learning how our staging services can enhance your listings?</p>
                
                <p>Best regards,<br>
                Gagan Arora<br>
                Design Gaga<br>
                Luxury Home Staging</p>
                </body>
                </html>
            """,
            'delay_hours': 24
        },
        {
            'subject': "Staged Properties Sell for 10-15% More in {location}",
            'html_content': """
                <html>
                <body>
                <p>Hi {name},</p>
                
                <p>I wanted to follow up and share that our staged properties in {location} typically 
                sell for 10-15% above market value. I'd love to show you our portfolio and discuss 
                how we can help your listings stand out.</p>
                
                <p>When would be a good time for a quick chat?</p>
                
                <p>Best regards,<br>
                Gagan Arora<br>
                Design Gaga<br>
                Luxury Home Staging</p>
                </body>
                </html>
            """,
            'delay_hours': 48
        },
        {
            'subject': "Special Offer for {location} Real Estate Agents",
            'html_content': """
                <html>
                <body>
                <p>Hi {name},</p>
                
                <p>I wanted to reach out one last time to let you know that we currently have 
                availability in {location} and are offering a special rate for first-time 
                collaborations.</p>
                
                <p>Would you be open to a quick discussion about how we can help your properties 
                sell faster and for more?</p>
                
                <p>Best regards,<br>
                Gagan Arora<br>
                Design Gaga<br>
                Luxury Home Staging</p>
                </body>
                </html>
            """,
            'delay_hours': 72
        }
    ]
    
    # Example target list
    target_list = [
        {
            'name': input("Enter agent name: "),
            'email': input("Enter agent email: "),
            'location': input("Enter location: ")
        }
    ]
    
    # Create campaign
    campaign_id = campaign.create_campaign(
        name="Home Staging Outreach",
        message_sequence=message_sequence,
        target_list=target_list
    )
    
    print(f"\nStarting campaign: {campaign_id}")
    print("\nCampaign will send:")
    print("1. Introduction and value proposition")
    print("2. Portfolio offer with success metrics")
    print("3. Special offer for first-time collaboration")
    print("\nProgress will be logged in email_campaign.log")
    
    # Get current stats
    stats = await campaign.get_campaign_stats()
    print("\n📊 Campaign Statistics:")
    print(f"Daily Limit: {stats['total_daily_limit']}")
    print(f"Sent Today: {stats['emails_sent_today']}")
    print(f"Remaining: {stats['remaining_daily_quota']}")
    
    # Run first campaign step
    await campaign.run_campaign_step(campaign_id)

if __name__ == "__main__":
    asyncio.run(main())
