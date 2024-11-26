from base_agent import BaseAgent
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path
import openai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from twilio.rest import Client
from jinja2 import Template
import requests
from campaign_config import CampaignConfig, MessageConfig

class CommunicationAgent(BaseAgent):
    def __init__(self, work_dir):
        super().__init__("Communication", work_dir)
        
        # Load API keys from environment
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_whatsapp = os.getenv('TWILIO_WHATSAPP_NUMBER')
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_pass = os.getenv('SMTP_PASS')
        self.sender_email = os.getenv('SENDER_EMAIL')
        
        # Load configurations
        self.campaign_config = CampaignConfig()
        
        # Initialize clients
        self.twilio_client = Client(self.twilio_sid, self.twilio_token)
        openai.api_key = self.openai_key
        
        # Load templates
        self.templates_dir = self.work_dir / 'templates'
        self.templates_dir.mkdir(exist_ok=True)
        self.load_templates()
        
        # Initialize message history
        self.history_dir = self.work_dir / 'message_history'
        self.history_dir.mkdir(exist_ok=True)
        
    def load_templates(self):
        """Load message templates"""
        self.templates = {
            'email': {
                'follow_up': self._load_template('email_follow_up.j2'),
                'welcome': self._load_template('email_welcome.j2'),
                'proposal': self._load_template('email_proposal.j2')
            },
            'sms': {
                'follow_up': self._load_template('sms_follow_up.j2'),
                'reminder': self._load_template('sms_reminder.j2')
            },
            'whatsapp': {
                'follow_up': self._load_template('whatsapp_follow_up.j2'),
                'update': self._load_template('whatsapp_update.j2')
            }
        }
        
    def _load_template(self, template_name: str) -> Template:
        """Load a single template file"""
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            self._create_default_template(template_path)
        return Template(template_path.read_text())
        
    def _create_default_template(self, template_path: Path):
        """Create default template if not exists"""
        if 'email' in template_path.name:
            content = """
            Dear {{ lead.name }},
            
            I hope this email finds you well. {{ custom_intro }}
            
            {% if lead.score >= 80 %}
            I noticed your interest in our luxury home staging services, particularly {{ lead.interests|join(', ') }}.
            {% endif %}
            
            {{ main_content }}
            
            Best regards,
            {{ sender.name }}
            Design Gaga
            """
        elif 'sms' in template_path.name:
            content = """
            Hi {{ lead.name }}! {{ main_content }} 
            
            Reply STOP to unsubscribe.
            """
        else:  # WhatsApp
            content = """
            Hello {{ lead.name }}! 👋
            
            {{ main_content }}
            
            Best regards,
            Design Gaga 🏠✨
            """
            
        template_path.write_text(content)
        
    def draft_message(self, lead_data: Dict, channel: str, template_type: str) -> str:
        """Draft a personalized message using AI"""
        try:
            # Get lead context
            context = self._get_lead_context(lead_data)
            
            # Generate personalized content using GPT
            prompt = self._create_prompt(context, channel, template_type)
            content = self._generate_content(prompt)
            
            # Render template
            template = self.templates[channel][template_type]
            message = template.render(
                lead=lead_data,
                custom_intro=content['intro'],
                main_content=content['main'],
                sender={'name': 'Sarah'}  # Replace with actual sender info
            )
            
            return message.strip()
            
        except Exception as e:
            self.logger.error(f"Message drafting failed: {str(e)}")
            return None
            
    def _get_lead_context(self, lead_data: Dict) -> Dict:
        """Get relevant context for the lead"""
        return {
            'name': lead_data.get('name', ''),
            'score': lead_data.get('score', 0),
            'interests': lead_data.get('interests', []),
            'recent_interactions': lead_data.get('recent_activities', []),
            'engagement_level': 'high' if lead_data.get('score', 0) >= 80 else 'medium',
            'last_contact': lead_data.get('last_contact')
        }
        
    def _create_prompt(self, context: Dict, channel: str, template_type: str) -> str:
        """Create prompt for GPT"""
        return f"""
        Draft a personalized {channel} {template_type} message for a luxury home staging lead.
        
        Lead Context:
        - Name: {context['name']}
        - Engagement Level: {context['engagement_level']}
        - Interests: {', '.join(context['interests'])}
        - Recent Interactions: {context['recent_interactions']}
        
        Guidelines:
        - Tone: Professional yet warm
        - Style: Luxury-focused
        - Length: {'Short and concise' if channel in ['sms', 'whatsapp'] else 'Detailed but focused'}
        - Include: Personalized observations about their interests
        - Call to Action: Clear next steps
        
        Format:
        {
            "intro": "Personalized introduction",
            "main": "Main message content"
        }
        """
        
    def _generate_content(self, prompt: str) -> Dict:
        """Generate content using GPT"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a luxury home staging expert."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return json.loads(response.choices[0].message.content)
        
    def send_email(self, to_email: str, subject: str, content: str):
        """Send an email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
                
            self._log_message('email', to_email, content)
            return True
            
        except Exception as e:
            self.logger.error(f"Email sending failed: {str(e)}")
            return False
            
    def send_sms(self, to_number: str, content: str):
        """Send an SMS"""
        try:
            message = self.twilio_client.messages.create(
                body=content,
                from_=self.twilio_whatsapp,
                to=to_number
            )
            
            self._log_message('sms', to_number, content)
            return True
            
        except Exception as e:
            self.logger.error(f"SMS sending failed: {str(e)}")
            return False
            
    def send_whatsapp(self, to_number: str, content: str):
        """Send a WhatsApp message"""
        try:
            message = self.twilio_client.messages.create(
                body=content,
                from_=f"whatsapp:{self.twilio_whatsapp}",
                to=f"whatsapp:{to_number}"
            )
            
            self._log_message('whatsapp', to_number, content)
            return True
            
        except Exception as e:
            self.logger.error(f"WhatsApp sending failed: {str(e)}")
            return False
            
    def _log_message(self, channel: str, recipient: str, content: str):
        """Log sent message"""
        log_file = self.history_dir / f"{channel}_history.json"
        
        try:
            if log_file.exists():
                history = json.loads(log_file.read_text())
            else:
                history = []
                
            history.append({
                'timestamp': datetime.now().isoformat(),
                'recipient': recipient,
                'content': content
            })
            
            log_file.write_text(json.dumps(history, indent=2))
            
        except Exception as e:
            self.logger.error(f"Message logging failed: {str(e)}")
            
    def run_campaign(self, leads: List[Dict], campaign_type: str):
        """Run an automated campaign across channels"""
        results = []
        campaign = self.campaign_config.get_campaign(campaign_type)
        
        for lead in leads:
            try:
                # Get first step
                current_step = campaign['steps'][0]
                
                # Check conditions
                if not self._check_conditions(lead, current_step.message.conditions):
                    continue
                    
                # Get channel and check if we can send
                channel = current_step.message.channel
                if not self.campaign_config.can_send_message(lead, channel):
                    self.schedule_message(lead, current_step, campaign['priority'])
                    continue
                    
                # Draft and send message
                message = self.draft_message(
                    lead,
                    channel,
                    current_step.message.template
                )
                
                if message:
                    # Send based on channel
                    success = self._send_message(lead, channel, message)
                    
                    # Schedule next step if needed
                    if success and current_step.next_steps:
                        self._schedule_next_steps(lead, current_step.next_steps, campaign)
                        
                    results.append({
                        'lead': lead['email'],
                        'channel': channel,
                        'success': success
                    })
                    
            except Exception as e:
                self.logger.error(f"Campaign send failed for {lead['email']}: {str(e)}")
                results.append({
                    'lead': lead['email'],
                    'error': str(e)
                })
                
        return results
        
    def _check_conditions(self, lead: Dict, conditions: Dict) -> bool:
        """Check if lead meets conditions"""
        for condition, value in conditions.items():
            if condition == 'score_min' and lead.get('score', 0) < value:
                return False
            elif condition == 'no_response' and lead.get('last_response'):
                last_response = datetime.fromisoformat(lead['last_response'])
                if datetime.now() - last_response < timedelta(hours=48):
                    return False
            elif condition == 'opened_previous' and not lead.get('opened_last_email'):
                return False
            elif condition == 'days_inactive':
                last_activity = datetime.fromisoformat(lead.get('last_activity', lead['first_seen']))
                if (datetime.now() - last_activity).days < value:
                    return False
                    
        return True
        
    def schedule_message(self, lead: Dict, step: CampaignStep, priority: str):
        """Schedule a message for later"""
        # Get next available send time
        send_time = self.campaign_config.get_next_send_time(step.message.channel, priority)
        
        # Add delay if specified
        if step.message.delay_hours > 0:
            send_time = (datetime.combine(datetime.now().date(), send_time) + 
                        timedelta(hours=step.message.delay_hours)).time()
            
        # Schedule task
        schedule.every().day.at(send_time.strftime("%H:%M")).do(
            self._send_scheduled_message,
            lead=lead,
            step=step
        ).tag(f"message_{lead['email']}")
        
    def _send_scheduled_message(self, lead: Dict, step: CampaignStep):
        """Send a scheduled message"""
        try:
            # Check conditions again
            if not self._check_conditions(lead, step.message.conditions):
                return False
                
            # Draft and send
            message = self.draft_message(
                lead,
                step.message.channel,
                step.message.template
            )
            
            if message:
                return self._send_message(lead, step.message.channel, message)
                
        except Exception as e:
            self.logger.error(f"Scheduled message failed: {str(e)}")
            return False
            
    def _send_message(self, lead: Dict, channel: str, message: str) -> bool:
        """Send message through specified channel"""
        try:
            if channel == 'email':
                success = self.send_email(
                    lead['email'],
                    f"Design Gaga: {message['subject']}",
                    message['content']
                )
            elif channel == 'sms':
                success = self.send_sms(lead['phone'], message)
            elif channel == 'whatsapp':
                success = self.send_whatsapp(lead['phone'], message)
                
            if success:
                # Update lead's last message time
                lead['last_message'] = {
                    'channel': channel,
                    'timestamp': datetime.now().isoformat()
                }
                
            return success
            
        except Exception as e:
            self.logger.error(f"Message sending failed: {str(e)}")
            return False
            
    def _schedule_next_steps(self, lead: Dict, next_steps: List[str], campaign: Dict):
        """Schedule next steps in campaign"""
        for step_name in next_steps:
            for step in campaign['steps']:
                if step.message.template == step_name:
                    self.schedule_message(lead, step, campaign['priority'])
                    break
                    
    def schedule_follow_up(self, lead_data: Dict, delay_hours: int = 24):
        """Schedule a follow-up message"""
        send_time = datetime.now() + timedelta(hours=delay_hours)
        
        # Create task for scheduler
        schedule.every().day.at(send_time.strftime("%H:%M")).do(
            self.run_campaign,
            [lead_data],
            'follow_up'
        ).tag(f"follow_up_{lead_data['email']}")
        
        self.logger.info(f"Scheduled follow-up for {lead_data['email']} at {send_time}")
