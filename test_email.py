import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_credentials():
    with open('agents/credentials.json', 'r') as f:
        return json.load(f)

def test_email_connection():
    # Load credentials
    creds = load_credentials()
    email_creds = creds['EMAIL']
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = f"{email_creds['sender_name']} <{email_creds['from_email']}>"
    msg['To'] = email_creds['from_email']  # Send to self for testing
    msg['Subject'] = "Test Email - Luxury Real Estate Campaign"
    
    body = f"""
    Hello {email_creds['sender_name']},
    
    This is a test email to verify your SMTP settings for the Luxury Real Estate Campaign.
    
    Configuration:
    - SMTP Host: {email_creds['smtp_host']}
    - From: {email_creds['sender_name']} ({email_creds['sender_title']})
    - Company: {email_creds['sender_company']}
    
    If you received this email, your email configuration is working correctly!
    
    Best regards,
    Your Campaign System
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Connect to SMTP server
        server = smtplib.SMTP(email_creds['smtp_host'], int(email_creds['smtp_port']))
        server.starttls()
        
        # Login
        server.login(email_creds['smtp_username'], email_creds['smtp_password'])
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        print("✅ Test email sent successfully!")
        print(f"Check your inbox at {email_creds['from_email']}")
        return True
        
    except Exception as e:
        print("❌ Error sending test email:")
        print(str(e))
        return False

if __name__ == "__main__":
    test_email_connection()
