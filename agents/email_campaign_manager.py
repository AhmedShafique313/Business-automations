import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from jinja2 import Template
import aiosmtplib
from tenacity import retry, stop_after_attempt, wait_exponential
from campaign_manager import BaseCampaignManager

class EmailCampaignManager(BaseCampaignManager):
    """Manages personalized email campaigns for luxury real estate agents"""
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        """Initialize email campaign manager"""
        self.setup_logging()
        self.credentials = self._load_credentials(credentials_path)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.setup_templates()
        
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
        self.logger = logging.getLogger('EmailCampaignManager')
        
    def _load_credentials(self, credentials_path: str) -> Dict:
        """Load email credentials from file"""
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                return creds.get('EMAIL', {})
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            return {}
            
    def setup_templates(self):
        """Set up email templates for different campaign types"""
        self.templates = {
            'initial_contact': Template("""
Dear {{ agent_name }},

I hope this email finds you well. I came across your impressive portfolio of luxury real estate listings in {{ location }} and was particularly impressed by your expertise in {{ strengths[0] if strengths else 'luxury properties' }}.

Design Gaga is a premium interior design and staging company that specializes in preparing luxury properties for market. We've helped numerous high-end properties achieve faster sales and higher valuations through our tailored staging and design services.

I would love to explore how we could collaborate to enhance your luxury listings. Would you be open to a brief conversation about how our services could add value to your business?

Best regards,
[Your Name]
Design Gaga
            """),
            
            'follow_up': Template("""
Dear {{ agent_name }},

I wanted to follow up on my previous email regarding potential collaboration opportunities. Given your strong presence in {{ location }}'s luxury real estate market, I believe our premium staging services could be particularly valuable for your high-end listings.

Some recent results from our staging projects:
- 15% average increase in sale price
- 40% reduction in days on market
- Consistent 5-star feedback from luxury homeowners

Would you have 15 minutes this week for a quick call to discuss how we could work together?

Best regards,
[Your Name]
Design Gaga
            """),
            
            'market_update': Template("""
Dear {{ agent_name }},

I hope you're having a great week. I wanted to share some interesting insights from our recent luxury home staging projects in {{ location }} that might be valuable for your business.

We've noticed some emerging trends in buyer preferences:
{{ market_insights }}

Given your expertise in {{ strengths[0] if strengths else 'luxury properties' }}, I'd love to discuss how these trends might align with your current listings.

Best regards,
[Your Name]
Design Gaga
            """)
        }
        
    def create_email(self, agent_data: Dict, template_name: str) -> MIMEMultipart:
        """Create personalized email for an agent"""
        try:
            # Get template
            template = self.templates.get(template_name)
            if not template:
                raise ValueError(f"Template not found: {template_name}")
            
            # Add market insights if needed
            if template_name == 'market_update':
                agent_data['market_insights'] = self._generate_market_insights(agent_data['location'])
            
            # Generate email content
            email_content = template.render(**agent_data)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.credentials.get('email')
            msg['To'] = agent_data.get('email')
            
            # Set subject based on template
            subjects = {
                'initial_contact': f"Premium Staging Partnership Opportunity - Design Gaga",
                'follow_up': f"Following Up - Luxury Staging Services",
                'market_update': f"Luxury Market Insights - {agent_data.get('location')}"
            }
            msg['Subject'] = subjects.get(template_name, "Design Gaga - Luxury Staging Services")
            
            # Attach content
            msg.attach(MIMEText(email_content, 'plain'))
            return msg
            
        except Exception as e:
            self.logger.error(f"Error creating email: {str(e)}")
            return None
            
    def send_email(self, msg: MIMEMultipart) -> bool:
        """Send email using SMTP"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(
                    self.credentials.get('email'),
                    self.credentials.get('password')
                )
                server.send_message(msg)
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")
            return False
            
    def _generate_market_insights(self, location: str) -> str:
        """Generate market insights for a specific location"""
        insights = [
            "- Modern minimalist staging is showing 20% better reception in virtual tours",
            "- Properties with dedicated home offices are seeing 25% more inquiries",
            "- Outdoor living spaces have become a top-3 priority for luxury buyers",
            "- Smart home integration is increasingly influencing buying decisions"
        ]
        return "\n".join(insights)
        
    def process_new_agents(self, database_file: str = 'luxury_agents_database.csv'):
        """Process new agents and send initial contact emails"""
        try:
            # Read database
            df = pd.read_csv(database_file)
            
            # Get agents without initial contact
            new_agents = df[df['initial_contact_date'].isna()]
            
            for _, agent in new_agents.iterrows():
                # Create and send email
                msg = self.create_email(agent.to_dict(), 'initial_contact')
                if msg and self.send_email(msg):
                    # Update database
                    df.loc[df['name'] == agent['name'], 'initial_contact_date'] = datetime.now().strftime('%Y-%m-%d')
                    df.to_csv(database_file, index=False)
                    self.logger.info(f"Sent initial contact email to {agent['name']}")
                
                # Add delay between emails
                time.sleep(300)  # 5 minutes between emails
                
        except Exception as e:
            self.logger.error(f"Error processing new agents: {str(e)}")
            
    def send_follow_up_campaign(self, database_file: str = 'luxury_agents_database.csv'):
        """Send follow-up emails to agents who haven't responded"""
        try:
            # Read database
            df = pd.read_csv(database_file)
            
            # Get agents for follow-up
            follow_up_date = datetime.now() - timedelta(days=7)
            follow_up_agents = df[
                (df['initial_contact_date'] <= follow_up_date.strftime('%Y-%m-%d')) &
                (df['follow_up_date'].isna()) &
                (df['response_received'] != True)
            ]
            
            for _, agent in follow_up_agents.iterrows():
                # Create and send follow-up email
                msg = self.create_email(agent.to_dict(), 'follow_up')
                if msg and self.send_email(msg):
                    # Update database
                    df.loc[df['name'] == agent['name'], 'follow_up_date'] = datetime.now().strftime('%Y-%m-%d')
                    df.to_csv(database_file, index=False)
                    self.logger.info(f"Sent follow-up email to {agent['name']}")
                
                # Add delay between emails
                time.sleep(300)  # 5 minutes between emails
                
        except Exception as e:
            self.logger.error(f"Error sending follow-up campaign: {str(e)}")
            
    def send_market_update_campaign(self, database_file: str = 'luxury_agents_database.csv'):
        """Send market update emails to all agents"""
        try:
            # Read database
            df = pd.read_csv(database_file)
            
            # Get agents for market update
            update_date = datetime.now() - timedelta(days=30)
            update_agents = df[
                (df['last_update_date'].isna()) |
                (df['last_update_date'] <= update_date.strftime('%Y-%m-%d'))
            ]
            
            for _, agent in update_agents.iterrows():
                # Create and send market update email
                msg = self.create_email(agent.to_dict(), 'market_update')
                if msg and self.send_email(msg):
                    # Update database
                    df.loc[df['name'] == agent['name'], 'last_update_date'] = datetime.now().strftime('%Y-%m-%d')
                    df.to_csv(database_file, index=False)
                    self.logger.info(f"Sent market update to {agent['name']}")
                
                # Add delay between emails
                time.sleep(300)  # 5 minutes between emails
                
        except Exception as e:
            self.logger.error(f"Error sending market update campaign: {str(e)}")

    async def send_message(self, agent_data: Dict, message: str) -> bool:
        """Send email message"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.credentials.get('email')
            msg['To'] = agent_data['email']
            
            # Set subject based on template
            subjects = {
                'initial_contact': f"Premium Staging Partnership Opportunity - Design Gaga",
                'follow_up': f"Following Up - Luxury Staging Services",
                'market_update': f"Luxury Market Insights - {agent_data.get('location')}"
            }
            msg['Subject'] = subjects.get('initial_contact', "Design Gaga - Luxury Staging Services")
            
            # Create HTML content
            html_content = self._format_email_content(message, agent_data)
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.smtp_server,
                port=self.smtp_port,
                use_tls=True
            ) as smtp:
                await smtp.login(
                    self.credentials.get('email'),
                    self.credentials.get('password')
                )
                await smtp.send_message(msg)
            
            self.logger.info(f"Email sent to {agent_data['email']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")
            return False

    async def process_response(self, response_data: Dict) -> Dict:
        """Process email response"""
        try:
            # Extract response content
            response_text = response_data.get('text', '')
            response_time = response_data.get('timestamp')
            
            # Analyze response
            analysis = await self.analyze_response(response_text)
            
            # Generate follow-up strategy
            follow_up = await self._generate_follow_up(analysis)
            
            return {
                'status': 'received',
                'response': response_text,
                'analysis': analysis,
                'next_steps': follow_up['steps'],
                'suggested_reply': follow_up['reply']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing email response: {str(e)}")
            return {}

    async def _generate_subject(self, agent_data: Dict) -> str:
        """Generate personalized email subject"""
        try:
            subject_prompt = {
                'agent_data': agent_data,
                'previous_subjects': self.learning_data.get('subjects', []),
                'successful_subjects': self.metrics.successful_templates
            }
            
            subject = await self.model_interface.generate_email_subject(subject_prompt)
            return subject
            
        except Exception as e:
            self.logger.error(f"Error generating subject: {str(e)}")
            return "Important: Luxury Real Estate Opportunity"

    async def _format_email_content(self, message: str, agent_data: Dict) -> str:
        """Format email content with HTML and personalization"""
        try:
            template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; }
                    .header { margin-bottom: 20px; }
                    .content { margin: 20px 0; }
                    .signature { margin-top: 30px; }
                    .footer { margin-top: 40px; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="header">
                    Dear {name},
                </div>
                <div class="content">
                    {message}
                </div>
                <div class="signature">
                    Best regards,<br>
                    {sender_name}<br>
                    {sender_title}<br>
                    {sender_company}
                </div>
                <div class="footer">
                    This email was sent to {email}.<br>
                    To unsubscribe, please click <a href="{unsubscribe_link}">here</a>
                </div>
            </body>
            </html>
            """
            
            return template.format(
                name=agent_data.get('name', 'Valued Agent'),
                message=message,
                sender_name=os.getenv('SENDER_NAME', 'Your Name'),
                sender_title=os.getenv('SENDER_TITLE', 'Luxury Real Estate Specialist'),
                sender_company=os.getenv('SENDER_COMPANY', 'Your Company'),
                email=agent_data.get('email', ''),
                unsubscribe_link=f"https://yourdomain.com/unsubscribe?email={agent_data.get('email', '')}"
            )
            
        except Exception as e:
            self.logger.error(f"Error formatting email: {str(e)}")
            return message

    async def _generate_follow_up(self, analysis: Dict) -> Dict:
        """Generate follow-up strategy based on response analysis"""
        try:
            strategy_prompt = {
                'sentiment': analysis.get('sentiment', 0),
                'intent': analysis.get('intent', 'unknown'),
                'key_points': analysis.get('key_points', []),
                'campaign_history': self.learning_data.get('follow_ups', [])
            }
            
            follow_up = await self.model_interface.generate_follow_up_strategy(strategy_prompt)
            return follow_up
            
        except Exception as e:
            self.logger.error(f"Error generating follow-up: {str(e)}")
            return {
                'steps': ['Send follow-up email in 3 days'],
                'reply': 'Thank you for your response. I will get back to you shortly.'
            }
