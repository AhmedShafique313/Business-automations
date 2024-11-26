from flask import Flask, request, redirect
import requests
import os

app = Flask(__name__)

# Replace these with your Asana app credentials
CLIENT_ID = '1208850627624477'
CLIENT_SECRET = 'd074489f3986c6d4685c282939b68857'
REDIRECT_URI = 'http://localhost:8001/callback'

@app.route('/callback')
def callback():
    # Get authorization code from the callback
    code = request.args.get('code')
    if not code:
        return "Error: No code provided"

    # Exchange authorization code for access token
    token_url = 'https://app.asana.com/-/oauth_token'
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code': code
    }
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        return f"Access Token: {access_token}"
    else:
        return f"Error: {response.json()}"

if __name__ == '__main__':
    app.run(port=8001)
