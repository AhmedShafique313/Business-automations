import httpx
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

class WebsiteAnalyzer:
    async def analyze(self, website_url: str) -> Dict[str, Any]:
        """
        Analyzes a website and returns insights about its structure, content, and performance.
        """
        logger.info(f"Starting website analysis for: {website_url}")
        try:
            async with httpx.AsyncClient() as client:
                # Fetch website content
                logger.info("Fetching website content...")
                response = await client.get(website_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                logger.info("Analyzing website structure...")
                # Basic analysis
                analysis = {
                    "title": soup.title.string if soup.title else None,
                    "meta_description": self._get_meta_description(soup),
                    "headers": self._analyze_headers(soup),
                    "links": self._analyze_links(soup),
                    "images": self._analyze_images(soup),
                    "social_media": self._find_social_media(soup),
                    "contact_info": self._find_contact_info(soup),
                    "performance_metrics": {
                        "load_time": response.elapsed.total_seconds(),
                        "size": len(response.content)
                    }
                }
                
                logger.info("Website analysis completed successfully")
                logger.info(f"Found {analysis['links']['total']} links, {analysis['images']['total']} images")
                logger.info(f"Page load time: {analysis['performance_metrics']['load_time']:.2f}s")
                
                return analysis
                
        except Exception as e:
            logger.error(f"Error analyzing website: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }

    def _get_meta_description(self, soup: BeautifulSoup) -> str:
        meta = soup.find('meta', attrs={'name': 'description'})
        desc = meta['content'] if meta else None
        logger.info(f"Meta description found: {'Yes' if desc else 'No'}")
        return desc

    def _analyze_headers(self, soup: BeautifulSoup) -> Dict[str, int]:
        headers = {}
        for i in range(1, 7):
            headers[f'h{i}'] = len(soup.find_all(f'h{i}'))
        logger.info(f"Header analysis: {headers}")
        return headers

    def _analyze_links(self, soup: BeautifulSoup) -> Dict[str, Any]:
        links = soup.find_all('a')
        external = len([l for l in links if l.get('href', '').startswith('http')])
        internal = len([l for l in links if l.get('href', '').startswith('/')])
        logger.info(f"Found {len(links)} total links ({external} external, {internal} internal)")
        return {
            "total": len(links),
            "external": external,
            "internal": internal
        }

    def _analyze_images(self, soup: BeautifulSoup) -> Dict[str, Any]:
        images = soup.find_all('img')
        with_alt = len([img for img in images if img.get('alt')])
        logger.info(f"Found {len(images)} images ({with_alt} with alt text)")
        return {
            "total": len(images),
            "with_alt": with_alt
        }

    def _find_social_media(self, soup: BeautifulSoup) -> Dict[str, str]:
        social_platforms = ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube']
        social_links = {}
        
        for link in soup.find_all('a'):
            href = link.get('href', '').lower()
            for platform in social_platforms:
                if platform in href:
                    social_links[platform] = href
                    logger.info(f"Found {platform} social media link")
                    
        return social_links

    def _find_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        contact_info = {}
        
        # Find email
        email_links = soup.find_all('a', href=lambda x: x and 'mailto:' in x)
        if email_links:
            contact_info['email'] = email_links[0]['href'].replace('mailto:', '')
            logger.info("Found email contact information")
            
        # Find phone
        phone_links = soup.find_all('a', href=lambda x: x and 'tel:' in x)
        if phone_links:
            contact_info['phone'] = phone_links[0]['href'].replace('tel:', '')
            logger.info("Found phone contact information")
            
        return contact_info
