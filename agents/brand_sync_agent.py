from base_agent import BaseAgent
import requests
from pathlib import Path
import hashlib
import shutil
import time
from PIL import Image
import io

class BrandSyncAgent(BaseAgent):
    def __init__(self, work_dir):
        super().__init__("BrandSync", work_dir)
        self.assets_dir = self.work_dir / 'brand_assets'
        self.assets_dir.mkdir(exist_ok=True)
        self.website_url = "https://designgaga.com"  # Replace with actual website URL
        self.asset_cache = {}
        
    def sync_brand_assets(self):
        """Synchronize brand assets from the website"""
        try:
            # Fetch main logo
            logo_url = f"{self.website_url}/assets/logo.png"  # Adjust path as needed
            self.sync_asset(logo_url, 'logo.png')
            
            # Fetch other brand assets
            assets = [
                '/assets/favicon.ico',
                '/assets/logo-dark.png',
                '/assets/logo-light.png'
            ]
            
            for asset_path in assets:
                asset_url = f"{self.website_url}{asset_path}"
                filename = Path(asset_path).name
                self.sync_asset(asset_url, filename)
                
            self.log_activity('brand_sync', 'completed')
            return True
            
        except Exception as e:
            self.log_activity('brand_sync', 'failed', {'error': str(e)})
            return False
            
    def sync_asset(self, url, filename):
        """Download and process a single brand asset"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Calculate file hash
            content = response.content
            file_hash = hashlib.md5(content).hexdigest()
            
            # Check if file has changed
            if self.asset_cache.get(filename) == file_hash:
                self.log_activity('asset_check', 'unchanged', {'file': filename})
                return False
                
            # Save new file
            asset_path = self.assets_dir / filename
            with open(asset_path, 'wb') as f:
                f.write(content)
                
            # Create different sizes for the logo
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                self.create_logo_variants(asset_path)
                
            self.asset_cache[filename] = file_hash
            self.log_activity('asset_update', 'completed', {
                'file': filename,
                'hash': file_hash
            })
            
            return True
            
        except Exception as e:
            self.log_activity('asset_sync', 'failed', {
                'file': filename,
                'error': str(e)
            })
            return False
            
    def create_logo_variants(self, logo_path):
        """Create different sizes of the logo for various platforms"""
        try:
            with Image.open(logo_path) as img:
                # Social media platform sizes
                sizes = {
                    'instagram': (1080, 1080),
                    'pinterest': (800, 450),
                    'twitter': (400, 400),
                    'facebook': (820, 312)
                }
                
                for platform, size in sizes.items():
                    resized = img.copy()
                    resized.thumbnail(size, Image.Resampling.LANCZOS)
                    
                    # Save with platform name
                    output_path = self.assets_dir / f"logo_{platform}.png"
                    resized.save(output_path, "PNG", quality=95)
                    
                self.log_activity('logo_variants', 'created', {
                    'original': str(logo_path),
                    'variants': list(sizes.keys())
                })
                
        except Exception as e:
            self.log_activity('logo_variants', 'failed', {'error': str(e)})
            
    def get_latest_logo(self, platform=None):
        """Get the path to the latest logo for a specific platform"""
        if platform:
            logo_path = self.assets_dir / f"logo_{platform}.png"
        else:
            logo_path = self.assets_dir / "logo.png"
            
        return str(logo_path) if logo_path.exists() else None
