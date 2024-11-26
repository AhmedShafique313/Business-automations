from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EmailProvider(ABC):
    """Abstract base class for email providers"""
    
    @abstractmethod
    async def send_welcome_email(self, recipient_email: str, recipient_name: str) -> bool:
        """Send welcome email to new user"""
        pass
    
    @abstractmethod
    async def send_notification(self, 
                              recipient_email: str, 
                              subject: str, 
                              message: str,
                              recipient_name: Optional[str] = None) -> bool:
        """Send notification email"""
        pass
