import json
import os
from getpass import getpass
import asyncio
from asana import Client as AsanaClient
import webbrowser
from typing import Dict, Any
import requests

def load_credentials() -> Dict[str, Any]:
    """Load existing credentials"""
    try:
        with open('agents/credentials.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_credentials(creds: Dict[str, Any]):
    """Save updated credentials"""
    with open('agents/credentials.json', 'w') as f:
        json.dump(creds, f, indent=4)

def setup_email():
    """Setup Gmail SMTP credentials"""
    print("\n=== Gmail SMTP Setup ===")
    print("Make sure you have:")
    print("1. Enabled 2-Step Verification in your Google Account")
    print("2. Generated an App Password for this application")
    print("\nEnter your Gmail credentials:")
    
    email = input("Gmail address: ")
    app_password = getpass("App Password (16 characters): ")
    name = input("Sender Name: ")
    title = input("Sender Title (e.g., Luxury Real Estate Specialist): ")
    company = input("Company Name: ")
    
    return {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": "587",
        "smtp_username": email,
        "smtp_password": app_password,
        "from_email": email,
        "sender_name": name,
        "sender_title": title,
        "sender_company": company
    }

async def setup_asana():
    """Setup Asana OAuth credentials"""
    print("\n=== Asana OAuth Setup ===")
    print("You'll need to:")
    print("1. Create an Asana Developer App if you haven't")
    print("2. Get your Client ID and Client Secret")
    print("3. Complete OAuth flow")
    
    client_id = input("Client ID: ")
    client_secret = getpass("Client Secret: ")
    
    # Initialize Asana client
    client = AsanaClient.oauth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://localhost:8000/oauth/callback"
    )
    
    # Get authorization URL
    (url, state) = client.session.authorization_url()
    print(f"\nOpen this URL in your browser to authorize:")
    print(url)
    
    webbrowser.open(url)
    auth_code = input("\nEnter the authorization code from the callback URL: ")
    
    # Get tokens
    token = client.session.fetch_token(code=auth_code)
    
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "tokens": {
            "access_token": token["access_token"],
            "refresh_token": token["refresh_token"],
            "expires_at": token["expires_at"]
        }
    }

def setup_whatsapp():
    """Setup WhatsApp Business API credentials"""
    print("\n=== WhatsApp Business API Setup ===")
    print("You'll need:")
    print("1. A WhatsApp Business Account")
    print("2. API Key from the Meta Developer Portal")
    print("3. Phone Number ID")
    print("4. Business Account ID")
    
    api_key = getpass("WhatsApp API Key: ")
    phone_number_id = input("Phone Number ID: ")
    business_account_id = input("Business Account ID: ")
    
    return {
        "api_key": api_key,
        "api_url": "https://graph.facebook.com/v17.0",
        "phone_number_id": phone_number_id,
        "business_account_id": business_account_id
    }

async def main():
    # Load existing credentials
    creds = load_credentials()
    
    print("Luxury Real Estate Campaign Credentials Setup")
    print("===========================================")
    
    while True:
        print("\nWhat would you like to set up?")
        print("1. Gmail SMTP (for email campaigns)")
        print("2. Asana (for task management)")
        print("3. WhatsApp Business API")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            creds["EMAIL"] = setup_email()
            save_credentials(creds)
            print("\n✅ Email credentials saved successfully!")
            
        elif choice == "2":
            creds["ASANA"] = await setup_asana()
            save_credentials(creds)
            print("\n✅ Asana credentials saved successfully!")
            
        elif choice == "3":
            creds["WHATSAPP"] = setup_whatsapp()
            save_credentials(creds)
            print("\n✅ WhatsApp credentials saved successfully!")
            
        elif choice == "4":
            print("\nSetup complete! You can run this script again anytime to update credentials.")
            break
        
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())
