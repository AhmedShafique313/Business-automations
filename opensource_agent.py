import json
import requests
from typing import Dict, List, Any
import os
from pathlib import Path

class OpenSourceAgent:
    def __init__(self, credentials_path: str = 'credentials_opensource.json'):
        self.credentials = self._load_credentials(credentials_path)
        self.services = {}
        self._initialize_services()

    def _load_credentials(self, path: str) -> Dict:
        with open(path, 'r') as f:
            return json.load(f)

    def _initialize_services(self):
        """Initialize connections to various services"""
        self._setup_ai_services()
        self._setup_social_media()
        self._setup_analytics()

    def _setup_ai_services(self):
        """Setup AI service connections"""
        if 'LOCAL_AI' in self.credentials['AI_SERVICES']:
            self.services['local_ai'] = {
                'endpoint': self.credentials['AI_SERVICES']['LOCAL_AI']['endpoint'],
                'models': self.credentials['AI_SERVICES']['LOCAL_AI']['models']
            }

    def _setup_social_media(self):
        """Setup social media connections"""
        if 'MASTODON' in self.credentials['SOCIAL_MEDIA']:
            self.services['mastodon'] = {
                'api_base': self.credentials['SOCIAL_MEDIA']['MASTODON']['api_base'],
                'access_token': self.credentials['SOCIAL_MEDIA']['MASTODON']['access_token']
            }

    def _setup_analytics(self):
        """Setup analytics connections"""
        if 'PLAUSIBLE' in self.credentials['ANALYTICS']:
            self.services['analytics'] = {
                'type': 'plausible',
                'site_id': self.credentials['ANALYTICS']['PLAUSIBLE']['site_id'],
                'api_key': self.credentials['ANALYTICS']['PLAUSIBLE']['api_key']
            }

    async def generate_content(self, prompt: str) -> str:
        """Generate content using available AI services"""
        try:
            # Try LocalAI first
            if 'local_ai' in self.services:
                response = requests.post(
                    f"{self.services['local_ai']['endpoint']}/v1/completions",
                    json={'prompt': prompt, 'model': self.services['local_ai']['models'][0]}
                )
                if response.status_code == 200:
                    return response.json()['choices'][0]['text']
        except Exception as e:
            print(f"Error with LocalAI: {e}")

        # Fallback to Meta AI if available
        if 'META_AI' in self.credentials['AI_SERVICES']:
            # Implementation for Meta AI
            pass

        return "Unable to generate content at this time."

    async def post_social_media(self, content: str, platforms: List[str] = None) -> Dict[str, bool]:
        """Post content to specified social media platforms"""
        results = {}
        platforms = platforms or ['mastodon', 'pixelfed', 'lemmy']

        for platform in platforms:
            if platform in self.services:
                try:
                    if platform == 'mastodon':
                        response = requests.post(
                            f"{self.services['mastodon']['api_base']}/statuses",
                            headers={'Authorization': f"Bearer {self.services['mastodon']['access_token']}"},
                            json={'status': content}
                        )
                        results[platform] = response.status_code == 200
                except Exception as e:
                    print(f"Error posting to {platform}: {e}")
                    results[platform] = False

        return results

    async def analyze_metrics(self) -> Dict[str, Any]:
        """Analyze metrics using configured analytics service"""
        if 'analytics' in self.services:
            try:
                if self.services['analytics']['type'] == 'plausible':
                    response = requests.get(
                        f"https://plausible.io/api/v1/stats/aggregate",
                        headers={'Authorization': f"Bearer {self.services['analytics']['api_key']}"},
                        params={'site_id': self.services['analytics']['site_id']}
                    )
                    if response.status_code == 200:
                        return response.json()
            except Exception as e:
                print(f"Error analyzing metrics: {e}")

        return {}

    async def store_media(self, file_path: str, bucket_name: str = None) -> str:
        """Store media using MinIO"""
        if 'MINIO' in self.credentials['STORAGE']:
            try:
                # Implementation for MinIO storage
                pass
            except Exception as e:
                print(f"Error storing media: {e}")
        return ""

if __name__ == "__main__":
    # Example usage
    agent = OpenSourceAgent()
    # Test the services
    import asyncio
    
    async def test_agent():
        content = await agent.generate_content("Write a post about open source software")
        print(f"Generated content: {content}")
        
        post_results = await agent.post_social_media(content, ['mastodon'])
        print(f"Posting results: {post_results}")
        
        metrics = await agent.analyze_metrics()
        print(f"Analytics metrics: {metrics}")
    
    asyncio.run(test_agent())
