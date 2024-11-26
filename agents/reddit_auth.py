import json
import webbrowser
import asyncio
import aiohttp
from aiohttp import web
import base64
import secrets
import urllib.parse

class RedditAuthServer:
    def __init__(self, creds_path="../credentials.json"):
        with open(creds_path, 'r') as f:
            self.creds = json.load(f)['REDDIT']
        self.state = secrets.token_urlsafe(32)
        self.app = web.Application()
        self.app.router.add_get('/reddit/callback', self.handle_callback)
        self.auth_response = None
        
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8081)
        await site.start()
        print("Server started at http://localhost:8081")
        
    def get_auth_url(self):
        params = {
            'client_id': self.creds['client_id'],
            'response_type': 'code',
            'state': self.state,
            'redirect_uri': self.creds['redirect_uri'],
            'duration': 'permanent',
            'scope': ' '.join(self.creds['scopes'])
        }
        return f"{self.creds['auth_url']}?{urllib.parse.urlencode(params)}"
    
    async def handle_callback(self, request):
        if request.query.get('state') != self.state:
            return web.Response(text="Invalid state parameter")
        
        if 'error' in request.query:
            return web.Response(text=f"Error: {request.query['error']}")
        
        code = request.query.get('code')
        if not code:
            return web.Response(text="No code received")
            
        # Exchange code for tokens
        auth_header = base64.b64encode(
            f"{self.creds['client_id']}:{self.creds['client_secret']}".encode()
        ).decode()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.creds['token_url'],
                headers={
                    'Authorization': f'Basic {auth_header}',
                    'User-Agent': self.creds['user_agent']
                },
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': self.creds['redirect_uri']
                }
            ) as resp:
                self.auth_response = await resp.json()
                
                if 'error' in self.auth_response:
                    return web.Response(text=f"Token Error: {self.auth_response['error']}")
                
                # Update credentials file
                self.creds['refresh_token'] = self.auth_response.get('refresh_token')
                self.creds['access_token'] = self.auth_response.get('access_token')
                
                with open("../credentials.json", 'r') as f:
                    all_creds = json.load(f)
                all_creds['REDDIT'] = self.creds
                
                with open("../credentials.json", 'w') as f:
                    json.dump(all_creds, f, indent=4)
                
                return web.Response(text="Authentication successful! You can close this window.")

async def main():
    auth_server = RedditAuthServer()
    await auth_server.start()
    
    auth_url = auth_server.get_auth_url()
    print(f"\nPlease open this URL in your browser to authenticate:")
    print(auth_url)
    
    # Open the URL in default browser
    webbrowser.open(auth_url)
    
    # Keep the server running
    while True:
        if auth_server.auth_response:
            print("\nAuthentication completed!")
            print("Tokens have been saved to credentials.json")
            break
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
