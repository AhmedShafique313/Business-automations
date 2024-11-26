import json
import requests
import logging
from typing import Dict, Optional

class WhatsAppTester:
    def __init__(self, credentials_path: str = 'agents/credentials.json'):
        """Initialize WhatsApp tester with credentials"""
        self.setup_logging()
        self.credentials = self._load_credentials(credentials_path)
        self.headers = {
            'Authorization': f'Bearer {self.credentials["api_key"]}',
            'Content-Type': 'application/json'
        }
        
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('whatsapp.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('WhatsAppTester')

    def _load_credentials(self, credentials_path: str) -> Dict:
        """Load WhatsApp credentials from file"""
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                return creds['WHATSAPP']
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            raise

    def send_template_message(self, to_number: str, template_name: str = "hello_world", language: str = "en_US") -> bool:
        """Send a template message"""
        url = f"{self.credentials['api_url']}/{self.credentials['phone_number_id']}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language
                }
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                self.logger.info("✅ Message sent successfully!")
                self.logger.info(f"Message ID: {response_data.get('messages', [{}])[0].get('id')}")
                return True
            else:
                self.logger.error("❌ Error sending message:")
                self.logger.error(response_data)
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error: {str(e)}")
            return False

    def send_text_message(self, to_number: str, message: str) -> bool:
        """Send a text message"""
        url = f"{self.credentials['api_url']}/{self.credentials['phone_number_id']}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                self.logger.info("✅ Message sent successfully!")
                self.logger.info(f"Message ID: {response_data.get('messages', [{}])[0].get('id')}")
                return True
            else:
                self.logger.error("❌ Error sending message:")
                self.logger.error(response_data)
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error: {str(e)}")
            return False

def main():
    # Initialize WhatsApp tester
    tester = WhatsAppTester()
    
    print("\nWhatsApp Message Tester")
    print("======================")
    print(f"\nFrom: {tester.credentials['test_number']}")
    
    # Get recipient number
    to_number = input("\nEnter recipient's phone number (with country code, e.g., +1234567890): ")
    
    while True:
        print("\nSelect message type:")
        print("1. Send template message (hello_world)")
        print("2. Send custom text message")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1":
            tester.send_template_message(to_number)
        elif choice == "2":
            message = input("\nEnter your message: ")
            tester.send_text_message(to_number, message)
        elif choice == "3":
            print("\nGoodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
