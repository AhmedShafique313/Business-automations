import os
from typing import Dict, List
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
from campaign_manager import BaseCampaignManager

class WhatsAppCampaignManager(BaseCampaignManager):
    def __init__(self):
        super().__init__('WhatsApp')
        self.whatsapp_config = self._load_whatsapp_config()
        
    def _load_whatsapp_config(self) -> Dict:
        """Load WhatsApp API configuration"""
        return {
            'api_key': os.getenv('WHATSAPP_API_KEY'),
            'api_url': os.getenv('WHATSAPP_API_URL', 'https://graph.facebook.com/v17.0'),
            'phone_number_id': os.getenv('WHATSAPP_PHONE_NUMBER_ID'),
            'business_account_id': os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def send_message(self, agent_data: Dict, message: str) -> bool:
        """Send WhatsApp message"""
        try:
            # Format the message with templates if available
            formatted_message = await self._format_whatsapp_message(message, agent_data)
            
            # Prepare the API request
            headers = {
                'Authorization': f"Bearer {self.whatsapp_config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': agent_data['phone'],
                'type': 'template' if formatted_message.get('template_name') else 'text',
                'template': formatted_message.get('template') if formatted_message.get('template_name') else None,
                'text': {'body': formatted_message['message']} if not formatted_message.get('template_name') else None
            }
            
            # Send message through WhatsApp Business API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.whatsapp_config['api_url']}/{self.whatsapp_config['phone_number_id']}/messages",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"WhatsApp message sent to {agent_data['phone']}")
                        return True
                    else:
                        self.logger.error(f"Error sending WhatsApp message: {await response.text()}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error sending WhatsApp message: {str(e)}")
            return False

    async def process_response(self, response_data: Dict) -> Dict:
        """Process WhatsApp response"""
        try:
            # Extract response content
            response_text = response_data.get('text', '')
            response_time = response_data.get('timestamp')
            message_type = response_data.get('type', 'text')
            
            # Handle different types of responses
            if message_type == 'text':
                analysis = await self.analyze_response(response_text)
            elif message_type == 'image':
                analysis = {'intent': 'shared_image', 'sentiment': 0.5}
            elif message_type == 'location':
                analysis = {'intent': 'shared_location', 'sentiment': 0.5}
            else:
                analysis = {'intent': 'unknown', 'sentiment': 0}
            
            # Generate follow-up strategy
            follow_up = await self._generate_follow_up(analysis, message_type)
            
            return {
                'status': 'received',
                'response': response_text,
                'type': message_type,
                'analysis': analysis,
                'next_steps': follow_up['steps'],
                'suggested_reply': follow_up['reply']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing WhatsApp response: {str(e)}")
            return {}

    async def _format_whatsapp_message(self, message: str, agent_data: Dict) -> Dict:
        """Format WhatsApp message with templates if available"""
        try:
            # Check if we have a template for this message type
            template_name = self._get_template_name(message, agent_data)
            
            if template_name:
                return {
                    'template_name': template_name,
                    'template': {
                        'name': template_name,
                        'language': {'code': 'en'},
                        'components': [
                            {
                                'type': 'body',
                                'parameters': [
                                    {'type': 'text', 'text': agent_data.get('name', 'Valued Agent')},
                                    {'type': 'text', 'text': message}
                                ]
                            }
                        ]
                    }
                }
            else:
                # Format as regular message
                formatted_message = f"Hi {agent_data.get('name', 'there')},\n\n{message}\n\nBest regards,\n{os.getenv('SENDER_NAME', 'Your Name')}"
                return {'message': formatted_message}
                
        except Exception as e:
            self.logger.error(f"Error formatting WhatsApp message: {str(e)}")
            return {'message': message}

    def _get_template_name(self, message: str, agent_data: Dict) -> str:
        """Determine appropriate template based on message content and agent data"""
        try:
            # Implement template selection logic based on message content
            if 'market update' in message.lower():
                return 'market_update'
            elif 'property alert' in message.lower():
                return 'property_alert'
            elif 'follow up' in message.lower():
                return 'follow_up'
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting template name: {str(e)}")
            return None

    async def _generate_follow_up(self, analysis: Dict, message_type: str) -> Dict:
        """Generate follow-up strategy based on response analysis"""
        try:
            strategy_prompt = {
                'sentiment': analysis.get('sentiment', 0),
                'intent': analysis.get('intent', 'unknown'),
                'message_type': message_type,
                'campaign_history': self.learning_data.get('follow_ups', [])
            }
            
            follow_up = await self.model_interface.generate_follow_up_strategy(strategy_prompt)
            return follow_up
            
        except Exception as e:
            self.logger.error(f"Error generating follow-up: {str(e)}")
            return {
                'steps': ['Send follow-up message in 24 hours'],
                'reply': 'Thank you for your response. I will get back to you shortly.'
            }

    async def handle_webhook(self, webhook_data: Dict):
        """Handle incoming webhook from WhatsApp Business API"""
        try:
            # Extract message data
            entry = webhook_data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])
            
            for message in messages:
                # Process each message
                response_data = {
                    'text': message.get('text', {}).get('body', ''),
                    'type': message.get('type', 'text'),
                    'timestamp': message.get('timestamp'),
                    'from': message.get('from')
                }
                
                # Process the response
                processed_response = await self.process_response(response_data)
                
                # Update Asana if we have a task ID for this conversation
                if value.get('task_gid'):
                    await self.update_task(value['task_gid'], processed_response)
                
        except Exception as e:
            self.logger.error(f"Error handling webhook: {str(e)}")
