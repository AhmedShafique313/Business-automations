import json
import logging
from twilio.rest import Client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Load credentials
    with open('agents/credentials.json', 'r') as f:
        credentials = json.load(f)
    logger.info("Credentials loaded successfully")
    
    # Log non-sensitive info for debugging
    logger.info(f"Using Twilio number: {credentials['TWILIO']['phone_number']}")
    logger.info("Target number: +14379878666")

    # Initialize Twilio client
    twilio_client = Client(
        credentials['TWILIO']['account_sid'],
        credentials['TWILIO']['auth_token']
    )
    logger.info("Twilio client initialized")

    # Make the test call
    call = twilio_client.calls.create(
        twiml='<Response><Say>Hello, this is Design Gaga calling about our luxury home staging services in the Greater Toronto Area.</Say></Response>',
        to='+14379878666',
        from_=credentials['TWILIO']['phone_number']
    )
    
    logger.info(f"Call initiated with SID: {call.sid}")
    
except Exception as e:
    logger.error(f"Error making call: {e}")
    logger.error(f"Error details: {str(e)}")
