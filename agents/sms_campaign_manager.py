import os
from typing import Dict, List
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from tenacity import retry, stop_after_attempt, wait_exponential
from campaign_manager import BaseCampaignManager

class SMSCampaignManager(BaseCampaignManager):
    def __init__(self):
        super().__init__('SMS')
        self.twilio_client = self._setup_twilio()
        
    def _setup_twilio(self) -> Client:
        """Set up Twilio client"""
        try:
            return Client(
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            )
        except Exception as e:
            self.logger.error(f"Error setting up Twilio client: {str(e)}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def send_message(self, agent_data: Dict, message: str) -> bool:
        """Send SMS message"""
        try:
            # Format message based on learning data and agent preferences
            formatted_message = await self._format_sms_message(message, agent_data)
            
            # Send message through Twilio
            message = self.twilio_client.messages.create(
                body=formatted_message,
                from_=os.getenv('TWILIO_PHONE_NUMBER'),
                to=agent_data['phone']
            )
            
            self.logger.info(f"SMS sent to {agent_data['phone']}, SID: {message.sid}")
            return True
            
        except TwilioRestException as e:
            self.logger.error(f"Twilio error sending SMS: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending SMS: {str(e)}")
            return False

    async def process_response(self, response_data: Dict) -> Dict:
        """Process SMS response"""
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
            self.logger.error(f"Error processing SMS response: {str(e)}")
            return {}

    async def _format_sms_message(self, message: str, agent_data: Dict) -> str:
        """Format SMS message with personalization"""
        try:
            # Get optimal message length from learning data
            optimal_length = self._get_optimal_length()
            
            # Format the message
            formatted_message = f"Hi {agent_data.get('name', 'there')}, {message}"
            
            # Add signature if space permits
            signature = f"\n- {os.getenv('SENDER_NAME', 'Your Name')}"
            if len(formatted_message) + len(signature) <= optimal_length:
                formatted_message += signature
            
            # Truncate if necessary while preserving meaning
            if len(formatted_message) > optimal_length:
                formatted_message = formatted_message[:optimal_length-3] + "..."
            
            return formatted_message
            
        except Exception as e:
            self.logger.error(f"Error formatting SMS: {str(e)}")
            return message

    def _get_optimal_length(self) -> int:
        """Determine optimal message length based on learning data"""
        try:
            if len(self.learning_data) < 10:
                return 160  # Standard SMS length
                
            # Analyze success rates by message length
            length_success = self.learning_data.groupby(
                pd.cut(self.learning_data['message_length'], bins=[0, 50, 100, 160, 320])
            ).agg({
                'response_received': 'mean',
                'converted': 'mean'
            })
            
            length_success['score'] = (
                length_success['response_received'] * 0.4 + 
                length_success['converted'] * 0.6
            )
            
            # Get the most successful length range
            best_range = length_success['score'].idxmax()
            return best_range.right
            
        except Exception as e:
            self.logger.error(f"Error getting optimal length: {str(e)}")
            return 160

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
                'steps': ['Send follow-up SMS in 48 hours'],
                'reply': 'Thank you for your response. I will get back to you shortly.'
            }

    async def handle_webhook(self, webhook_data: Dict):
        """Handle incoming webhook from Twilio"""
        try:
            # Extract message data
            response_data = {
                'text': webhook_data.get('Body', ''),
                'timestamp': webhook_data.get('DateCreated'),
                'from': webhook_data.get('From')
            }
            
            # Process the response
            processed_response = await self.process_response(response_data)
            
            # Update Asana if we have a task ID for this conversation
            conversation_sid = webhook_data.get('ConversationSid')
            if conversation_sid and hasattr(self, 'conversation_tasks'):
                task_gid = self.conversation_tasks.get(conversation_sid)
                if task_gid:
                    await self.update_task(task_gid, processed_response)
            
        except Exception as e:
            self.logger.error(f"Error handling webhook: {str(e)}")

    def _sanitize_phone_number(self, phone: str) -> str:
        """Sanitize phone number to E.164 format"""
        try:
            # Remove any non-numeric characters
            clean_number = ''.join(filter(str.isdigit, phone))
            
            # Add country code if missing
            if len(clean_number) == 10:  # US number without country code
                clean_number = f"+1{clean_number}"
            elif not clean_number.startswith('+'):
                clean_number = f"+{clean_number}"
                
            return clean_number
            
        except Exception as e:
            self.logger.error(f"Error sanitizing phone number: {str(e)}")
            return phone
