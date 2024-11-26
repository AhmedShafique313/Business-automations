import json
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
from pathlib import Path
from communication_tracker import CommunicationTracker

class WhatsAppCampaign:
    def __init__(self, credentials_path: str = 'agents/credentials.json'):
        """Initialize WhatsApp Campaign Manager"""
        self.setup_logging()
        self.credentials = self._load_credentials(credentials_path)
        self.headers = {
            'Authorization': f'Bearer {self.credentials["api_key"]}',
            'Content-Type': 'application/json'
        }
        self.campaign_data_path = Path('agents/campaign_data')
        self.campaign_data_path.mkdir(exist_ok=True)
        self.tracker = CommunicationTracker(credentials_path)
        
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('whatsapp_campaign.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('WhatsAppCampaign')

    def _load_credentials(self, credentials_path: str) -> Dict:
        """Load WhatsApp credentials from file"""
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                return creds['WHATSAPP']
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            raise

    def create_campaign(self, name: str, message_sequence: List[Dict], target_list: List[Dict]) -> str:
        """
        Create a new campaign with message sequence and target list
        
        Args:
            name: Campaign name
            message_sequence: List of message templates/texts with delays
            target_list: List of target contacts with their data
        
        Returns:
            campaign_id: Unique identifier for the campaign
        """
        campaign_id = f"{name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        campaign_data = {
            'id': campaign_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'message_sequence': message_sequence,
            'target_list': target_list,
            'progress': {contact['phone']: {'current_step': 0, 'last_message': None} 
                        for contact in target_list}
        }
        
        # Save campaign data
        with open(self.campaign_data_path / f"{campaign_id}.json", 'w') as f:
            json.dump(campaign_data, f, indent=2)
            
        self.logger.info(f"Created campaign: {campaign_id}")
        return campaign_id

    async def send_campaign_message(self, contact: Dict, message_data: Dict) -> bool:
        """Send a campaign message to a contact"""
        url = f"{self.credentials['api_url']}/{self.credentials['phone_number_id']}/messages"
        
        # Personalize message with contact data
        if message_data['type'] == 'template':
            payload = {
                "messaging_product": "whatsapp",
                "to": contact['phone'],
                "type": "template",
                "template": {
                    "name": message_data['template_name'],
                    "language": {
                        "code": message_data.get('language', 'en_US')
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": param.format(**contact)}
                                for param in message_data.get('parameters', [])
                            ]
                        }
                    ]
                }
            }
        else:  # text message
            message_text = message_data['text'].format(**contact)
            payload = {
                "messaging_product": "whatsapp",
                "to": contact['phone'],
                "type": "text",
                "text": {
                    "body": message_text
                }
            }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                self.logger.info(f"✅ Message sent to {contact['phone']}")
                # Track the message in Asana
                await self.tracker.track_whatsapp_message(contact, message_data, 'Sent')
                return True
            else:
                self.logger.error(f"❌ Error sending message to {contact['phone']}:")
                self.logger.error(response_data)
                # Track the failed message
                await self.tracker.track_whatsapp_message(contact, message_data, 'Failed')
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error: {str(e)}")
            # Track the error
            await self.tracker.track_whatsapp_message(contact, message_data, f'Error: {str(e)}')
            return False

    async def run_campaign(self, campaign_id: str):
        """Run a campaign, sending messages according to the sequence"""
        campaign_file = self.campaign_data_path / f"{campaign_id}.json"
        
        if not campaign_file.exists():
            self.logger.error(f"Campaign {campaign_id} not found")
            return
            
        with open(campaign_file, 'r') as f:
            campaign = json.load(f)
            
        while campaign['status'] == 'active':
            for contact in campaign['target_list']:
                progress = campaign['progress'][contact['phone']]
                current_step = progress['current_step']
                
                if current_step >= len(campaign['message_sequence']):
                    continue
                    
                last_message = progress['last_message']
                message_data = campaign['message_sequence'][current_step]
                
                # Check if it's time to send the next message
                if last_message is None or (
                    datetime.fromisoformat(last_message) + 
                    timedelta(hours=message_data['delay_hours']) <= datetime.now()
                ):
                    if await self.send_campaign_message(contact, message_data):
                        progress['current_step'] += 1
                        progress['last_message'] = datetime.now().isoformat()
                        
                        # Save progress
                        with open(campaign_file, 'w') as f:
                            json.dump(campaign, f, indent=2)
            
            # Check if campaign is complete
            if all(progress['current_step'] >= len(campaign['message_sequence']) 
                   for progress in campaign['progress'].values()):
                campaign['status'] = 'completed'
                with open(campaign_file, 'w') as f:
                    json.dump(campaign, f, indent=2)
                self.logger.info(f"Campaign {campaign_id} completed!")
                break
                
            await asyncio.sleep(60)  # Check every minute

def main():
    # Example usage
    campaign = WhatsAppCampaign()
    
    # Example message sequence
    message_sequence = [
        {
            'type': 'template',
            'template_name': 'hello_world',
            'language': 'en_US',
            'delay_hours': 0
        },
        {
            'type': 'text',
            'text': "Hi {name}, I noticed you're a successful agent in {location}. "
                   "I'd love to discuss how we can help grow your luxury real estate business.",
            'delay_hours': 24
        },
        {
            'type': 'text',
            'text': "Hi {name}, just following up. Would you be interested in a quick chat about "
                   "how we've helped other agents in {location} increase their luxury listings?",
            'delay_hours': 48
        }
    ]
    
    # Example target list
    target_list = [
        {
            'name': 'John Smith',
            'phone': '+1234567890',
            'location': 'Beverly Hills',
            'specialty': 'Luxury Homes'
        }
    ]
    
    # Create and run campaign
    campaign_id = campaign.create_campaign(
        name="Luxury Agent Outreach",
        message_sequence=message_sequence,
        target_list=target_list
    )
    
    print(f"\nCreated campaign: {campaign_id}")
    print("\nTo run the campaign:")
    print("    await campaign.run_campaign(campaign_id)")

if __name__ == "__main__":
    main()
