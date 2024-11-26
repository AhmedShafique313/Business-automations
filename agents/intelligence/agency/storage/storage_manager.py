"""
Storage manager for handling content and analytics data.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class StorageManager:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = str(Path(__file__).parents[4])  # Root project directory
        
        self.base_dir = Path(base_dir)
        self.storage_dirs = {
            'content': self.base_dir / 'data' / 'content',
            'analytics': self.base_dir / 'data' / 'analytics',
            'reports': self.base_dir / 'data' / 'reports',
            'models': self.base_dir / 'data' / 'models',
            'logs': self.base_dir / 'logs'
        }
        
        # Create all necessary directories
        for dir_path in self.storage_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def store_content(self, content: Dict[str, Any], platform: str, industry: str) -> str:
        """Store generated content with metadata."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{platform}_{industry}_{timestamp}.json"
        filepath = self.storage_dirs['content'] / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                'metadata': {
                    'platform': platform,
                    'industry': industry,
                    'timestamp': timestamp,
                    'version': '1.0'
                },
                'content': content
            }, f, indent=2)
        
        return str(filepath)
    
    def store_analytics(self, analytics_data: Dict[str, Any], analysis_type: str) -> str:
        """Store analytics results."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{analysis_type}_{timestamp}.json"
        filepath = self.storage_dirs['analytics'] / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                'metadata': {
                    'type': analysis_type,
                    'timestamp': timestamp,
                    'version': '1.0'
                },
                'data': analytics_data
            }, f, indent=2)
        
        return str(filepath)
    
    def store_report(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Store generated reports."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_{timestamp}.json"
        filepath = self.storage_dirs['reports'] / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                'metadata': {
                    'type': report_type,
                    'timestamp': timestamp,
                    'version': '1.0'
                },
                'report': report_data
            }, f, indent=2)
        
        return str(filepath)
    
    def get_model_path(self, model_name: str) -> str:
        """Get path for storing/loading model files."""
        return str(self.storage_dirs['models'] / model_name)
    
    def get_latest_content(self, platform: Optional[str] = None, 
                          industry: Optional[str] = None,
                          limit: int = 10) -> list:
        """Retrieve latest content, optionally filtered by platform/industry."""
        content_dir = self.storage_dirs['content']
        files = sorted(content_dir.glob('*.json'), key=os.path.getmtime, reverse=True)
        
        results = []
        for file in files:
            if len(results) >= limit:
                break
                
            with open(file) as f:
                data = json.load(f)
                
            if platform and data['metadata']['platform'] != platform:
                continue
            if industry and data['metadata']['industry'] != industry:
                continue
                
            results.append(data)
            
        return results
    
    def get_latest_analytics(self, analysis_type: Optional[str] = None,
                           limit: int = 10) -> list:
        """Retrieve latest analytics results."""
        analytics_dir = self.storage_dirs['analytics']
        files = sorted(analytics_dir.glob('*.json'), key=os.path.getmtime, reverse=True)
        
        results = []
        for file in files:
            if len(results) >= limit:
                break
                
            with open(file) as f:
                data = json.load(f)
                
            if analysis_type and data['metadata']['type'] != analysis_type:
                continue
                
            results.append(data)
            
        return results
