"""
Content Storage Manager
Manages storage and retrieval of generated content across platforms.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentStore:
    """Manages storage of generated content and associated metadata."""
    
    def __init__(self, base_path: str = "content_store"):
        """Initialize the content store."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different content types
        self.structure = {
            'text': self.base_path / 'text',
            'images': self.base_path / 'images',
            'videos': self.base_path / 'videos',
            'metadata': self.base_path / 'metadata'
        }
        
        for path in self.structure.values():
            path.mkdir(exist_ok=True)
            
    async def store_content(self, content_data: Dict) -> str:
        """
        Store content and its metadata.
        
        Args:
            content_data: Dictionary containing content and metadata
            
        Returns:
            str: Content ID for future reference
        """
        try:
            content_id = content_data.get('id', datetime.now().strftime('%Y%m%d_%H%M%S'))
            content_type = content_data.get('type', 'text')
            
            # Store the actual content
            content_path = self.structure[content_type] / f"{content_id}"
            if isinstance(content_data['content'], (str, dict)):
                with open(content_path.with_suffix('.json'), 'w') as f:
                    json.dump(content_data['content'], f, indent=2)
            else:
                # For binary content (images, videos)
                with open(content_path.with_suffix(self._get_extension(content_type)), 'wb') as f:
                    f.write(content_data['content'])
                    
            # Store metadata
            metadata = {
                'id': content_id,
                'type': content_type,
                'platform': content_data.get('platform'),
                'created_at': datetime.now().isoformat(),
                'industry': content_data.get('industry'),
                'target_audience': content_data.get('target_audience', []),
                'performance_metrics': content_data.get('performance_metrics', {}),
                'tags': content_data.get('tags', []),
                'related_leads': content_data.get('related_leads', [])
            }
            
            metadata_path = self.structure['metadata'] / f"{content_id}_meta.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Stored content {content_id} of type {content_type}")
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to store content: {e}")
            raise
            
    async def get_content(self, content_id: str) -> Optional[Dict]:
        """Retrieve content and its metadata by ID."""
        try:
            # Get metadata first
            metadata_path = self.structure['metadata'] / f"{content_id}_meta.json"
            if not metadata_path.exists():
                logger.warning(f"Content {content_id} not found")
                return None
                
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            # Get the actual content
            content_path = self.structure[metadata['type']] / content_id
            if metadata['type'] in ['text', 'json']:
                with open(content_path.with_suffix('.json'), 'r') as f:
                    content = json.load(f)
            else:
                with open(content_path.with_suffix(self._get_extension(metadata['type'])), 'rb') as f:
                    content = f.read()
                    
            return {
                'content': content,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve content {content_id}: {e}")
            return None
            
    async def update_content_metadata(self, content_id: str, updates: Dict) -> bool:
        """Update metadata for existing content."""
        try:
            metadata_path = self.structure['metadata'] / f"{content_id}_meta.json"
            if not metadata_path.exists():
                logger.warning(f"Content {content_id} not found")
                return False
                
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            # Update metadata
            metadata.update(updates)
            metadata['updated_at'] = datetime.now().isoformat()
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Updated metadata for content {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update content metadata: {e}")
            return False
            
    async def list_content(
        self,
        content_type: Optional[str] = None,
        platform: Optional[str] = None,
        industry: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """List content matching specified criteria."""
        try:
            results = []
            metadata_dir = self.structure['metadata']
            
            for meta_file in metadata_dir.glob('*_meta.json'):
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                    
                # Apply filters
                if content_type and metadata['type'] != content_type:
                    continue
                if platform and metadata['platform'] != platform:
                    continue
                if industry and metadata['industry'] != industry:
                    continue
                    
                created_at = datetime.fromisoformat(metadata['created_at'])
                if start_date and created_at < start_date:
                    continue
                if end_date and created_at > end_date:
                    continue
                    
                results.append(metadata)
                
            return sorted(results, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list content: {e}")
            return []
            
    async def delete_content(self, content_id: str) -> bool:
        """Delete content and its metadata."""
        try:
            # Get metadata to know content type
            metadata_path = self.structure['metadata'] / f"{content_id}_meta.json"
            if not metadata_path.exists():
                logger.warning(f"Content {content_id} not found")
                return False
                
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            # Delete content file
            content_path = self.structure[metadata['type']] / content_id
            if content_path.with_suffix('.json').exists():
                content_path.with_suffix('.json').unlink()
            if content_path.with_suffix(self._get_extension(metadata['type'])).exists():
                content_path.with_suffix(self._get_extension(metadata['type'])).unlink()
                
            # Delete metadata
            metadata_path.unlink()
            
            logger.info(f"Deleted content {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete content: {e}")
            return False
            
    def _get_extension(self, content_type: str) -> str:
        """Get file extension for content type."""
        extensions = {
            'text': '.txt',
            'image': '.png',
            'video': '.mp4',
            'json': '.json'
        }
        return extensions.get(content_type, '.bin')
        
    async def cleanup_old_content(self, days: int = 30) -> int:
        """Clean up content older than specified days."""
        try:
            cleanup_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            for meta_file in self.structure['metadata'].glob('*_meta.json'):
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                    
                created_at = datetime.fromisoformat(metadata['created_at'])
                if created_at < cleanup_date:
                    if await self.delete_content(metadata['id']):
                        deleted_count += 1
                        
            logger.info(f"Cleaned up {deleted_count} old content items")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to clean up old content: {e}")
            return 0
