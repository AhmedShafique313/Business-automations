import json
import logging
from pathlib import Path
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

class StorageService:
    """Service for handling object storage using MinIO"""
    
    def __init__(self):
        credentials_path = Path(__file__).parent.parent.parent.parent / 'credentials.json'
        with open(credentials_path) as f:
            self.credentials = json.load(f)
        
        minio_config = self.credentials['STORAGE']['MINIO']
        self.client = Minio(
            minio_config['endpoint'],
            access_key=minio_config['access_key'],
            secret_key=minio_config['secret_key'],
            secure=minio_config['secure']
        )
        
    def _ensure_bucket(self, bucket_name: str) -> bool:
        """Ensure bucket exists, create if it doesn't"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            return True
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {str(e)}")
            return False
            
    async def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_data: BinaryIO,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """Upload a file to MinIO storage"""
        try:
            if not self._ensure_bucket(bucket_name):
                return None
                
            self.client.put_object(
                bucket_name,
                object_name,
                file_data,
                file_data.seek(0, 2),  # Get file size
                content_type=content_type
            )
            
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading file: {str(e)}")
            return None
            
    async def download_file(self, bucket_name: str, object_name: str) -> Optional[bytes]:
        """Download a file from MinIO storage"""
        try:
            data = self.client.get_object(bucket_name, object_name)
            return data.read()
            
        except S3Error as e:
            logger.error(f"Error downloading file: {str(e)}")
            return None
            
    async def delete_file(self, bucket_name: str, object_name: str) -> bool:
        """Delete a file from MinIO storage"""
        try:
            self.client.remove_object(bucket_name, object_name)
            return True
            
        except S3Error as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
            
    async def list_files(self, bucket_name: str, prefix: Optional[str] = None) -> Optional[list]:
        """List files in a bucket with optional prefix"""
        try:
            if not self._ensure_bucket(bucket_name):
                return None
                
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
            
        except S3Error as e:
            logger.error(f"Error listing files: {str(e)}")
            return None
