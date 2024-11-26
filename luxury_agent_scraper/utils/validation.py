import re
from typing import Dict
from .errors import ValidationError

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return True  # Empty email is allowed
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    if not phone:
        return True  # Empty phone is allowed
    # Remove all non-numeric characters
    phone = re.sub(r'\D', '', phone)
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(phone) <= 15

def validate_url(url: str) -> bool:
    """Validate URL format"""
    if not url:
        return True  # Empty URL is allowed
    pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    return bool(re.match(pattern, url))

def validate_social_handle(handle: str) -> bool:
    """Validate social media handle format"""
    if not handle:
        return True  # Empty handle is allowed
    # Basic validation - no spaces, special characters limited
    pattern = r'^[A-Za-z0-9_.-]+$'
    return bool(re.match(pattern, handle))

def validate_agent_data(data: Dict) -> Dict:
    """
    Validate agent data
    
    Args:
        data (Dict): Agent data to validate
        
    Returns:
        Dict: Validated and cleaned data
        
    Raises:
        ValidationError: If validation fails
    """
    # Required fields
    if not data.get('name'):
        raise ValidationError("Agent name is required")
    
    if not data.get('location'):
        raise ValidationError("Location is required")
    
    # Validate email
    if not validate_email(data.get('email', '')):
        raise ValidationError(f"Invalid email format: {data.get('email')}")
    
    # Validate phone
    if not validate_phone(data.get('phone', '')):
        raise ValidationError(f"Invalid phone format: {data.get('phone')}")
    
    # Validate URLs
    for url_field in ['website_url', 'linkedin_url', 'source_url']:
        if not validate_url(data.get(url_field, '')):
            raise ValidationError(f"Invalid URL format for {url_field}: {data.get(url_field)}")
    
    # Validate social handles
    for handle_field in ['instagram_handle', 'facebook_handle', 'twitter_handle']:
        if not validate_social_handle(data.get(handle_field, '')):
            raise ValidationError(f"Invalid handle format for {handle_field}: {data.get(handle_field)}")
    
    # Clean data
    cleaned_data = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in data.items()
    }
    
    return cleaned_data
