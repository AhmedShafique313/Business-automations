"""
Asana OAuth Integration
Handles OAuth authentication flow for Asana.
"""

import os
import logging
from pathlib import Path
from typing import Optional
import secrets
from dotenv import load_dotenv
from flask import Flask, request, session, redirect, url_for

# Import from local auth package using relative import
from .auth.auth_manager import AuthManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('asana_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Initialize Auth Manager
auth_manager = AuthManager()

@app.route('/')
def index():
    """Initiate OAuth flow."""
    try:
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        # Get authorization URL
        auth_url = auth_manager.get_authorization_url('asana', state)
        logger.info(f"Generated authorization URL: {auth_url}")
        
        return f'''
        <html>
            <body>
                <h1>Design Gaga Marketing Automation</h1>
                <p>Click below to connect with Asana:</p>
                <a href="{auth_url}" style="
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #4A90E2;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-family: Arial, sans-serif;
                ">Connect with Asana</a>
                <p>Debug Info:</p>
                <pre>
                Authorization URL: {auth_url}
                State: {state}
                </pre>
            </body>
        </html>
        '''
        
    except Exception as e:
        logger.error(f"Error initiating OAuth flow: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/oauth/callback')
async def oauth_callback():
    """Handle OAuth callback."""
    try:
        # Verify state parameter
        state = request.args.get('state')
        stored_state = session.pop('oauth_state', None)
        
        if not state or not stored_state or state != stored_state:
            raise ValueError("Invalid state parameter")
        
        # Exchange code for token
        code = request.args.get('code')
        if not code:
            raise ValueError("No authorization code received")
        
        token_data = await auth_manager.exchange_code_for_token('asana', code, state)
        logger.info("Successfully exchanged code for token")
        
        return '''
        <html>
            <body>
                <h1>Successfully Connected!</h1>
                <p>Your Asana account has been successfully connected to Design Gaga Marketing Automation.</p>
                <p>You can now close this window and return to the application.</p>
            </body>
        </html>
        '''
        
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        return f'''
        <html>
            <body>
                <h1>Authentication Error</h1>
                <p>An error occurred during authentication:</p>
                <pre>{str(e)}</pre>
                <p>Please try again or contact support if the problem persists.</p>
            </body>
        </html>
        ''', 500

if __name__ == '__main__':
    # Set up work directory
    work_dir = Path(os.getenv('WORK_DIR', '/mnt/VANDAN_DISK/code_stuff/projects/experiments/agents/work'))
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # Enable insecure transport for local development
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    # Run Flask app
    app.run(host='localhost', port=8888, debug=True)
