"""Memory management utility for efficient resource usage."""

import logging
import gc
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from prometheus_client import Gauge

# Prometheus metrics
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Current memory usage in bytes')
CACHE_SIZE = Gauge('cache_size_bytes', 'Current cache size in bytes')

class MemoryManager:
    """Manages memory usage and caching for the system."""
    
    def __init__(self, max_cache_size: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.max_cache_size = max_cache_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_cleanup = datetime.now()
        
    async def cache_data(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Cache data with optional TTL in seconds."""
        try:
            # Check cache size and cleanup if needed
            if len(self._cache) >= self.max_cache_size:
                await self.cleanup_cache()
                
            # Store data with metadata
            self._cache[key] = {
                'data': data,
                'timestamp': datetime.now(),
                'ttl': ttl,
                'size': self._estimate_size(data)
            }
            
            # Update metrics
            self._update_metrics()
            
        except Exception as e:
            self.logger.error(f"Error caching data: {str(e)}")
            
    async def get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve cached data if available and not expired."""
        try:
            if key in self._cache:
                cache_entry = self._cache[key]
                
                # Check if data has expired
                if cache_entry['ttl']:
                    expiry_time = cache_entry['timestamp'] + timedelta(seconds=cache_entry['ttl'])
                    if datetime.now() > expiry_time:
                        del self._cache[key]
                        return None
                        
                return cache_entry['data']
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving cached data: {str(e)}")
            return None
            
    async def cleanup_cache(self) -> None:
        """Clean up expired cache entries and run garbage collection."""
        try:
            current_time = datetime.now()
            
            # Remove expired entries
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry['ttl'] and current_time > entry['timestamp'] + timedelta(seconds=entry['ttl'])
            ]
            
            for key in expired_keys:
                del self._cache[key]
                
            # Run garbage collection if needed
            if (current_time - self._last_cleanup).total_seconds() > 3600:  # 1 hour
                gc.collect()
                self._last_cleanup = current_time
                
            # Update metrics
            self._update_metrics()
            
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {str(e)}")
            
    def _estimate_size(self, data: Any) -> int:
        """Estimate memory size of data in bytes."""
        try:
            return len(str(data).encode('utf-8'))
        except:
            return 0
            
    def _update_metrics(self) -> None:
        """Update Prometheus metrics."""
        try:
            total_cache_size = sum(entry['size'] for entry in self._cache.values())
            CACHE_SIZE.set(total_cache_size)
            MEMORY_USAGE.set(gc.get_stats()[0]['size'])
        except Exception as e:
            self.logger.error(f"Error updating metrics: {str(e)}")
