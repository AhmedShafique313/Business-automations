import os
import json
import logging
from typing import Dict, Optional
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from openai import OpenAI
import pandas as pd
from datetime import datetime
from flask import Flask, request
from urllib.parse import urljoin
import time

app = Flask(__name__)

class IntelligentCaller:
    def __init__(self, credentials_path: str = 'credentials.json'):
        """Initialize the intelligent caller with necessary credentials"""
        self.setup_logging()
        self.credentials = self._load_credentials(credentials_path)
        self.initialize_clients()
        
    def setup_logging(self):
        """Set up logging for the caller agent"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('intelligent_caller.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('IntelligentCaller')

    def _load_credentials(self, credentials_path: str) -> Dict:
        """Load API credentials from file"""
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                return {
                    'TWILIO': creds.get('TWILIO', {}),
                    'OPENAI': creds.get('OPENAI', {})
                }
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            return {}

    def initialize_clients(self):
        """Initialize Twilio and OpenAI clients"""
        try:
            # Initialize Twilio client
            twilio_creds = self.credentials['TWILIO']
            self.twilio_client = Client(
                twilio_creds.get('account_sid'),
                twilio_creds.get('auth_token')
            )
            self.twilio_number = twilio_creds.get('phone_number')
            
            # Initialize OpenAI client
            self.openai_client = OpenAI(
                api_key=self.credentials['OPENAI'].get('api_key')
            )
            
            self.logger.info("Successfully initialized Twilio and OpenAI clients")
            
        except Exception as e:
            self.logger.error(f"Error initializing clients: {str(e)}")

    def generate_call_script(self, agent_info: Dict) -> str:
        """Generate a personalized call script using OpenAI"""
        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an AI assistant helping to generate a professional and engaging call script for a luxury real estate agent in the Greater Toronto Area."},
                    {"role": "user", "content": f"Generate a brief, natural-sounding introduction script for a call to a potential client. The script should introduce Design Gaga's luxury home staging services and mention the agent's name: {agent_info.get('name')}"},
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error generating call script: {e}")
            return "Hello, this is Design Gaga calling about our luxury home staging services in the Greater Toronto Area."

    def make_call(self, agent_info: Dict) -> Optional[str]:
        """Initiate a call to an agent"""
        try:
            # Generate call script
            script = self.generate_call_script(agent_info)
            
            # Store script for webhook access
            self.current_script = script
            
            # Make the call
            call = self.twilio_client.calls.create(
                to=agent_info['phone'],
                from_=self.twilio_number,
                url=urljoin(self.credentials['TWILIO'].get('webhook_base_url'), '/voice'),
                status_callback=urljoin(self.credentials['TWILIO'].get('webhook_base_url'), '/status'),
                status_callback_event=['initiated', 'ringing', 'answered', 'completed']
            )
            
            self.logger.info(f"Initiated call to {agent_info['name']}: {call.sid}")
            return call.sid
            
        except Exception as e:
            self.logger.error(f"Error making call: {e}")
            return None

    def process_agent_response(self, response: str) -> str:
        """Process agent's response using OpenAI"""
        try:
            prompt = f"""
            The real estate agent just said: "{response}"
            
            Generate an appropriate response that:
            1. Acknowledges their input
            2. Maintains professional tone
            3. Moves the conversation forward
            4. If positive, suggest next steps
            5. If negative, thank them politely and end call
            
            Keep it natural and conversational.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a professional luxury home staging company representative."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error processing response: {e}")
            return "I apologize, but I need to transfer you to a human representative. Someone will follow up with you shortly."

    def log_call_result(self, call_sid: str, agent_info: Dict, status: str, notes: str = ""):
        """Log call results to a CSV file"""
        try:
            call_log = {
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'agent_name': agent_info['name'],
                'brokerage': agent_info['brokerage'],
                'phone': agent_info['phone'],
                'call_sid': call_sid,
                'status': status,
                'notes': notes
            }
            
            df = pd.DataFrame([call_log])
            
            # Append to existing log or create new one
            log_file = 'call_logs.csv'
            if os.path.exists(log_file):
                df.to_csv(log_file, mode='a', header=False, index=False)
            else:
                df.to_csv(log_file, index=False)
                
            self.logger.info(f"Logged call result for {agent_info['name']}")
            
        except Exception as e:
            self.logger.error(f"Error logging call result: {e}")

# Flask routes for Twilio webhooks
@app.route('/voice', methods=['POST'])
def voice():
    """Handle incoming voice webhook"""
    response = VoiceResponse()
    
    # Get the current script from the IntelligentCaller instance
    script = app.caller.current_script
    
    # Add initial pause
    response.pause(length=1)
    
    # Read the script
    response.say(script, voice='Polly.Matthew')
    
    # Gather the response
    gather = Gather(input='speech', timeout=3, language='en-US')
    response.append(gather)
    
    return str(response)

@app.route('/status', methods=['POST'])
def status():
    """Handle call status webhook"""
    call_sid = request.values.get('CallSid')
    status = request.values.get('CallStatus')
    
    # Log status update
    logging.info(f"Call {call_sid} status: {status}")
    
    return '', 200

if __name__ == "__main__":
    # Initialize the caller
    caller = IntelligentCaller()
    app.caller = caller  # Make caller accessible to Flask routes
    
    try:
        # Test call to specific number
        test_agent = {
            'name': 'Test Agent',
            'brokerage': 'GTA Luxury Homes',
            'phone': '4379878666',
            'location': 'Toronto, ON',
            'source': 'Test',
            'date_found': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Make the test call
        call_sid = caller.make_call(test_agent)
        
        if call_sid:
            # Log initial call attempt
            caller.log_call_result(
                call_sid=call_sid,
                agent_info=test_agent,
                status='initiated'
            )
        
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        
    # Start Flask server for webhooks
    app.run(port=5000)
