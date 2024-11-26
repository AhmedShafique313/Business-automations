import logging
from typing import Optional
from .base import EmailProvider
from ...config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockEmailProvider(EmailProvider):
    """Mock email provider for development and testing"""
    
    def __init__(self):
        logger.info("Initializing Mock Email Provider")

    async def send_welcome_email(self, recipient_email: str, recipient_name: str) -> bool:
        """
        Send a welcome email to the user. In mock mode, this just logs the email content.
        
        Args:
            recipient_email: The email address of the recipient
            recipient_name: The name of the recipient
            
        Returns:
            bool: True if the email would have been sent successfully
        """
        try:
            # Log the email content
            logger.info(f"MOCK EMAIL: Sending welcome email to {recipient_name} ({recipient_email})")
            logger.info("Email Content:")
            logger.info("-" * 50)
            logger.info(f"To: {recipient_name} <{recipient_email}>")
            logger.info("Subject: Welcome to AI Business Platform!")
            logger.info("Body:")
            logger.info(f"""
Hi {recipient_name},

Welcome to AI Business Platform! We're excited to have you on board.

You can now:
- Generate AI-powered content
- Manage your social media presence
- Analyze your business performance

Best regards,
The AI Business Platform Team
            """)
            logger.info("-" * 50)

            return True

        except Exception as e:
            logger.error(f"Error sending welcome email: {str(e)}")
            return False

    async def send_notification(self, 
                              recipient_email: str, 
                              subject: str, 
                              message: str,
                              recipient_name: Optional[str] = None) -> bool:
        """
        Send a notification email. In mock mode, this just logs the email content.
        
        Args:
            recipient_email: The email address of the recipient
            subject: The email subject
            message: The email message
            recipient_name: Optional name of the recipient
            
        Returns:
            bool: True if the email would have been sent successfully
        """
        try:
            # Log the email content
            logger.info(f"MOCK EMAIL: Sending notification to {recipient_email}")
            logger.info("Email Content:")
            logger.info("-" * 50)
            logger.info(f"To: {recipient_name or 'User'} <{recipient_email}>")
            logger.info(f"Subject: {subject}")
            logger.info("Body:")
            logger.info(message)
            logger.info("-" * 50)

            return True

        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False

class EmailService:
    """Factory class for creating email providers"""
    
    def __init__(self):
        settings = get_settings()
        self.provider = self._create_provider(settings.EMAIL_PROVIDER)
        
    def _create_provider(self, provider_type: str) -> EmailProvider:
        """Create the appropriate email provider based on configuration"""
        if provider_type == "mock":
            return MockEmailProvider()
        # Add other providers here as needed
        # elif provider_type == "mailjet":
        #     return MailjetProvider()
        # elif provider_type == "smtp":
        #     return SMTPProvider()
        else:
            logger.warning(f"Unknown provider type: {provider_type}, falling back to mock provider")
            return MockEmailProvider()
    
    async def send_welcome_email(self, recipient_email: str, recipient_name: str) -> bool:
        """Send welcome email using configured provider"""
        return await self.provider.send_welcome_email(recipient_email, recipient_name)
    
    async def send_notification(self, 
                              recipient_email: str, 
                              subject: str, 
                              message: str,
                              recipient_name: Optional[str] = None) -> bool:
        """Send notification using configured provider"""
        return await self.provider.send_notification(
            recipient_email, 
            subject, 
            message, 
            recipient_name
        )
