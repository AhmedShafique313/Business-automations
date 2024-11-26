import os
import json
import time
import random
import logging
import pandas as pd
from datetime import datetime, timedelta
from twilio.rest import Client
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from credentials_manager import CredentialsManager
from business_generator import BusinessGenerator
from asana_tasks import DesignGagaTasks

class OutreachManager:
    def __init__(self):
        """Initialize outreach manager with credentials and campaign settings"""
        self.logger = self._setup_logger()
        self.creds_manager = CredentialsManager()
        self.business_generator = BusinessGenerator()
        self.asana_manager = DesignGagaTasks()
        
        # Load campaign configuration
        with open('templates/design_gaga_campaign.json', 'r') as f:
            self.campaign_config = json.load(f)
        
        # Initialize API clients
        self._init_clients()
        
        # Load business info
        self.business_info = self.campaign_config['business_info']
        
        # Initialize campaign trackers
        self.contact_history = {}
        self.campaign_metrics = {
            'sms': {'sent': 0, 'responses': 0},
            'email': {'sent': 0, 'opens': 0, 'clicks': 0},
            'calls': {'made': 0, 'connected': 0, 'interested': 0}
        }

    def _setup_logger(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('outreach_manager.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def _init_clients(self):
        """Initialize API clients for different channels"""
        try:
            # Twilio for SMS and calls
            twilio_creds = self.creds_manager.get_credentials('TWILIO')
            self.twilio_client = Client(twilio_creds['account_sid'], twilio_creds['auth_token'])
            
            # SMTP for emails
            smtp_creds = self.creds_manager.get_credentials('SMTP')
            self.smtp_server = smtp_creds['server']
            self.smtp_user = smtp_creds['username']
            self.smtp_pass = smtp_creds['password']
            
        except Exception as e:
            self.logger.error(f"Error initializing clients: {str(e)}")
            raise

    def send_sms(self, contact, template_key='initial_message'):
        """Send SMS to a contact using specified template"""
        try:
            if not self._can_contact('sms', contact):
                return False
                
            # Get template
            template = self.campaign_config['outreach_campaigns']['sms'][contact['type'].lower()][template_key]
            
            # Personalize message
            message = template.format(
                name=contact['name'],
                area=contact.get('area', self.business_info['location'])
            )
            
            # Send SMS
            message = self.twilio_client.messages.create(
                to=contact['phone'],
                from_=self.business_info['phone'],
                body=message
            )
            
            # Update contact history
            self._update_contact_history(contact, 'sms', template_key)
            self.campaign_metrics['sms']['sent'] += 1
            
            self.logger.info(f"SMS sent to {contact['name']}: {message.sid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending SMS to {contact['name']}: {str(e)}")
            return False

    def send_email(self, contact, template_type='introduction'):
        """Send email to a contact using specified template"""
        try:
            if not self._can_contact('email', contact):
                return False
                
            # Get template
            template = self.campaign_config['outreach_campaigns']['email'][contact['type'].lower()]['templates'][template_type]
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = contact['email']
            msg['Subject'] = template['subject'].format(
                area=contact.get('area', self.business_info['location'])
            )
            
            # Personalize body
            body = template['body'].format(
                name=contact['name'],
                area=contact.get('area', self.business_info['location'])
            )
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            # Update contact history
            self._update_contact_history(contact, 'email', template_type)
            self.campaign_metrics['email']['sent'] += 1
            
            self.logger.info(f"Email sent to {contact['name']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email to {contact['name']}: {str(e)}")
            return False

    def schedule_follow_ups(self, contact):
        """Schedule follow-up communications based on campaign rules"""
        try:
            rules = self.campaign_config['automation_rules']['follow_up_timing']
            
            # Schedule email follow-ups
            if contact.get('email'):
                for i, delay in enumerate(['first', 'second', 'third']):
                    if i < rules['email']['max_attempts']:
                        delay_days = int(rules['email'][delay].split('_')[0])
                        follow_up_date = datetime.now() + timedelta(days=delay_days)
                        self._schedule_task(
                            'send_email',
                            follow_up_date,
                            contact,
                            'follow_up'
                        )
            
            # Schedule SMS follow-ups
            if contact.get('phone'):
                for i, delay in enumerate(['first', 'second']):
                    if i < rules['sms']['max_attempts']:
                        delay_days = int(rules['sms'][delay].split('_')[0])
                        follow_up_date = datetime.now() + timedelta(days=delay_days)
                        self._schedule_task(
                            'send_sms',
                            follow_up_date,
                            contact,
                            'follow_up'
                        )
            
        except Exception as e:
            self.logger.error(f"Error scheduling follow-ups for {contact['name']}: {str(e)}")

    def _schedule_task(self, task_type, execution_time, contact, template_type):
        """Schedule a task for future execution and create Asana task"""
        try:
            # Add to task queue (implement with actual task queue system)
            task = {
                'type': task_type,
                'execution_time': execution_time,
                'contact': contact,
                'template_type': template_type
            }
            
            # Create Asana task
            task_details = {
                'name': f"{task_type.title()} Follow-up: {contact['name']}",
                'notes': f'''
                Contact Details:
                - Name: {contact['name']}
                - Type: {contact.get('type', 'N/A')}
                - Email: {contact.get('email', 'N/A')}
                - Phone: {contact.get('phone', 'N/A')}
                - Area: {contact.get('area', 'N/A')}
                
                Task Details:
                - Type: {task_type}
                - Template: {template_type}
                - Scheduled: {execution_time.strftime('%Y-%m-%d %H:%M')}
                
                Previous Interactions:
                {self._get_contact_history_summary(contact)}
                ''',
                'due_on': execution_time.strftime('%Y-%m-%d'),
                'assignee': None  # Will be assigned based on task type
            }
            
            # Create task in appropriate section
            section_name = 'Customer Engagement' if task_type in ['email', 'sms'] else 'Lead Generation'
            sections = self.asana_manager.setup_sections()
            self.asana_manager.create_task(sections[section_name], task_details)
            
            # Log the scheduled task
            self.logger.info(f"Scheduled {task_type} for {contact['name']} at {execution_time}")
            
        except Exception as e:
            self.logger.error(f"Error scheduling task: {str(e)}")

    def _get_contact_history_summary(self, contact):
        """Generate a summary of contact history for Asana task notes"""
        contact_id = f"{contact['name']}_{contact.get('phone', '')}_{contact.get('email', '')}"
        history = self.contact_history.get(contact_id, {})
        
        summary = []
        for channel, interactions in history.items():
            for interaction in interactions:
                summary.append(
                    f"- {interaction['timestamp'].strftime('%Y-%m-%d %H:%M')}: "
                    f"{channel.upper()} - {interaction['template_type']}"
                )
        
        return '\n'.join(summary) if summary else 'No previous interactions'

    def _can_contact(self, channel, contact):
        """Check if we can contact this person through this channel"""
        try:
            # Check if we have necessary contact info
            if channel == 'sms' and not contact.get('phone'):
                return False
            if channel == 'email' and not contact.get('email'):
                return False
            
            # Check blackout periods
            now = datetime.now().time()
            rules = self.campaign_config['automation_rules']['blackout_periods'][channel]
            
            if now < datetime.strptime(rules['before'], '%H:%M').time():
                return False
            if now > datetime.strptime(rules['after'], '%H:%M').time():
                return False
            
            # Check contact history
            contact_id = f"{contact['name']}_{contact.get('phone', '')}_{contact.get('email', '')}"
            history = self.contact_history.get(contact_id, {}).get(channel, [])
            
            if len(history) >= self.campaign_config['automation_rules']['follow_up_timing'][channel]['max_attempts']:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking contact permissions: {str(e)}")
            return False

    def _update_contact_history(self, contact, channel, template_type):
        """Update contact history after each interaction"""
        try:
            contact_id = f"{contact['name']}_{contact.get('phone', '')}_{contact.get('email', '')}"
            
            if contact_id not in self.contact_history:
                self.contact_history[contact_id] = {}
            
            if channel not in self.contact_history[contact_id]:
                self.contact_history[contact_id][channel] = []
            
            self.contact_history[contact_id][channel].append({
                'timestamp': datetime.now(),
                'template_type': template_type
            })
            
        except Exception as e:
            self.logger.error(f"Error updating contact history: {str(e)}")

    def run_campaign(self, campaign_type='all'):
        """Run outreach campaign"""
        try:
            # Get target list
            targets = self.business_generator.generate_target_list()
            self.logger.info(f"Generated {len(targets)} potential targets")
            
            for contact in targets:
                # Score lead
                score = self._score_lead(contact)
                if score < self.campaign_config['lead_scoring']['minimum_score']:
                    continue
                
                # Send initial communications
                if campaign_type in ['all', 'email'] and contact.get('email'):
                    self.send_email(contact)
                    
                if campaign_type in ['all', 'sms'] and contact.get('phone'):
                    self.send_sms(contact)
                
                # Schedule follow-ups
                self.schedule_follow_ups(contact)
                
                # Pause between contacts
                time.sleep(random.randint(30, 60))
            
            return self.campaign_metrics
            
        except Exception as e:
            self.logger.error(f"Error running campaign: {str(e)}")
            return None

    def _score_lead(self, contact):
        """Score a lead based on defined criteria"""
        try:
            score = 0
            criteria = self.campaign_config['lead_scoring']['criteria']
            
            # Score based on property type
            if contact.get('property_type') in criteria['property_type']:
                score += criteria['property_type'][contact['property_type']]
            
            # Score based on location
            if contact.get('area') in criteria['location']:
                score += criteria['location'][contact['area']]
            
            # Score based on response rate (if available)
            if contact.get('response_rate') in criteria['response_rate']:
                score += criteria['response_rate'][contact['response_rate']]
            
            # Score based on transaction volume (if available)
            if contact.get('transaction_volume') in criteria['transaction_volume']:
                score += criteria['transaction_volume'][contact['transaction_volume']]
            
            return score
            
        except Exception as e:
            self.logger.error(f"Error scoring lead: {str(e)}")
            return 0

    def get_campaign_metrics(self):
        """Get current campaign metrics"""
        return {
            'metrics': self.campaign_metrics,
            'contact_history': len(self.contact_history),
            'active_campaigns': {
                'email': sum(1 for h in self.contact_history.values() if 'email' in h),
                'sms': sum(1 for h in self.contact_history.values() if 'sms' in h)
            }
        }

if __name__ == "__main__":
    # Initialize outreach manager
    manager = OutreachManager()
    
    # Run initial campaign
    print("\n🚀 Starting multi-channel outreach campaign for Design Gaga...")
    metrics = manager.run_campaign()
    
    # Print results
    print("\n📊 Campaign Results:")
    print(f"SMS: {metrics['sms']['sent']} sent, {metrics['sms']['responses']} responses")
    print(f"Email: {metrics['email']['sent']} sent, {metrics['email']['opens']} opens, {metrics['email']['clicks']} clicks")
    print(f"Calls: {metrics['calls']['made']} made, {metrics['calls']['connected']} connected, {metrics['calls']['interested']} interested")
