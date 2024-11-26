from flask import Flask, request
import requests
import json
from pathlib import Path
import urllib.parse

app = Flask(__name__)

CLIENT_ID = "1208846208913975"
CLIENT_SECRET = "2cd54ae4cfa4e2704c34a3ee83b1250c"
REDIRECT_URI = "http://localhost:8080/auth/callback"

def get_auth_url():
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'state': 'random_state'
    }
    return f"https://app.asana.com/-/oauth_authorize?{urllib.parse.urlencode(params)}"

@app.route('/auth/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return 'Error: No code received', 400
    
    # Exchange code for access token
    token_url = 'https://app.asana.com/-/oauth_token'
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code': code
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        return f'Error getting access token: {response.text}', 400
        
    tokens = response.json()
    
    # Update credentials.json
    creds_path = Path(__file__).parent / 'credentials.json'
    with open(creds_path) as f:
        creds = json.load(f)
    
    creds['ASANA']['tokens']['access_token'] = tokens['access_token']
    creds['ASANA']['tokens']['refresh_token'] = tokens.get('refresh_token')
    creds['ASANA']['tokens']['expires_at'] = tokens.get('expires_in')
    
    with open(creds_path, 'w') as f:
        json.dump(creds, f, indent=4)
        
    return 'Successfully got access token! You can close this window.'

if __name__ == '__main__':
    auth_url = get_auth_url()
    print("\nPlease visit this URL to authorize the application:")
    print(auth_url + "\n")
    app.run(port=8080, host='0.0.0.0')
