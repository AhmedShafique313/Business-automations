import json
import os
import webbrowser
import asyncio
from asana import Client as AsanaClient
import requests
from urllib.parse import urlencode
import http.server
import socketserver
import threading
from typing import Dict, Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Setup')

class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle OAuth callback"""
        if '/oauth/callback' in self.path:
            # Extract code from query parameters
            import urllib.parse
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            code = params.get('code', [None])[0]
            
            if code:
                # Store the code
                self.server.oauth_code = code
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_message = """
                <html>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                    <script>window.close();</script>
                </body>
                </html>
                """
                self.wfile.write(success_message.encode())
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'No authorization code found')

def load_credentials() -> Dict:
    """Load existing credentials"""
    try:
        with open('agents/credentials.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_credentials(creds: Dict):
    """Save updated credentials"""
    with open('agents/credentials.json', 'w') as f:
        json.dump(creds, f, indent=4)

def setup_whatsapp():
    """Setup WhatsApp Business API"""
    print("\n=== WhatsApp Business API Setup ===")
    print("\nFollow these steps:")
    print("1. Go to https://developers.facebook.com/")
    print("2. Create or select your Meta App")
    print("3. Add WhatsApp product to your app")
    print("4. Get your WhatsApp Business Account ID")
    print("5. Get your Phone Number ID")
    print("6. Generate a permanent token with whatsapp_business_messaging permission")
    
    print("\nEnter your WhatsApp Business API credentials:")
    api_key = input("Permanent Token: ")
    phone_number_id = input("Phone Number ID: ")
    business_account_id = input("Business Account ID: ")
    
    # Test the API connection
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("\n✅ WhatsApp API connection successful!")
            return {
                "api_key": api_key,
                "api_url": "https://graph.facebook.com/v17.0",
                "phone_number_id": phone_number_id,
                "business_account_id": business_account_id
            }
        else:
            print("\n❌ Error testing WhatsApp API connection:")
            print(response.json())
            return None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None

async def setup_asana():
    """Setup Asana OAuth"""
    print("\n=== Asana OAuth Setup ===")
    print("\nFollow these steps:")
    print("1. Go to https://app.asana.com/0/developer-console")
    print("2. Create a new app or select existing app")
    print("3. Get your Client ID and Client Secret")
    print("4. Add OAuth Redirect URL: http://localhost:8000/oauth/callback")
    
    client_id = input("\nEnter Client ID: ")
    client_secret = input("Enter Client Secret: ")
    
    # Start local server for OAuth callback
    server = socketserver.TCPServer(('localhost', 8000), OAuthCallbackHandler)
    server.oauth_code = None
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        # Initialize Asana client
        client = AsanaClient.oauth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://localhost:8000/oauth/callback"
        )
        
        # Get authorization URL
        (url, state) = client.session.authorization_url()
        print("\nOpening browser for Asana authorization...")
        webbrowser.open(url)
        
        # Wait for callback
        print("Waiting for authorization (check your browser)...")
        while server.oauth_code is None:
            await asyncio.sleep(1)
        
        # Exchange code for tokens
        token = client.session.fetch_token(code=server.oauth_code)
        
        print("\n✅ Asana OAuth setup successful!")
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "tokens": {
                "access_token": token["access_token"],
                "refresh_token": token.get("refresh_token"),
                "expires_at": token.get("expires_at")
            }
        }
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None
    finally:
        server.shutdown()
        server.server_close()

async def main():
    # Load existing credentials
    creds = load_credentials()
    
    # Setup WhatsApp
    whatsapp_creds = setup_whatsapp()
    if whatsapp_creds:
        creds['WHATSAPP'] = whatsapp_creds
        save_credentials(creds)
    
    # Setup Asana
    asana_creds = await setup_asana()
    if asana_creds:
        creds['ASANA'] = asana_creds
        save_credentials(creds)
    
    print("\nSetup complete! Check credentials.json for your updated configuration.")

if __name__ == "__main__":
    asyncio.run(main())
