import time
import asyncio
from collections import defaultdict
from .errors import RateLimitError

class AdaptiveRateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter with adaptive backoff
        
        Args:
            max_requests (int): Maximum number of requests allowed
            time_window (int): Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
        self.backoff_times = defaultdict(lambda: 1)
    
    def _clean_old_requests(self, domain: str):
        """Remove requests older than the time window"""
        current_time = time.time()
        self.requests[domain] = [
            req_time for req_time in self.requests[domain]
            if current_time - req_time <= self.time_window
        ]
    
    async def acquire(self, domain: str):
        """
        Acquire a rate limit slot with adaptive backoff
        
        Args:
            domain (str): Domain to rate limit
            
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        current_time = time.time()
        self._clean_old_requests(domain)
        
        if len(self.requests[domain]) >= self.max_requests:
            # Calculate wait time with exponential backoff
            wait_time = self.backoff_times[domain]
            self.backoff_times[domain] = min(wait_time * 2, 60)  # Cap at 60 seconds
            
            raise RateLimitError(
                f"Rate limit exceeded for {domain}. "
                f"Try again in {wait_time} seconds."
            )
        
        # Request successful, reset backoff
        self.backoff_times[domain] = 1
        self.requests[domain].append(current_time)
        
    async def wait_if_needed(self, domain: str):
        """Wait if rate limit would be exceeded"""
        try:
            await self.acquire(domain)
        except RateLimitError as e:
            wait_time = self.backoff_times[domain]
            await asyncio.sleep(wait_time)
            await self.acquire(domain)
