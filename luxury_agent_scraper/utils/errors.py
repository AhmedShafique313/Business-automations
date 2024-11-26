class ScrapingError(Exception):
    """Raised when there is an error during web scraping"""
    pass

class ValidationError(Exception):
    """Raised when data validation fails"""
    pass

class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass

class APIError(Exception):
    """Raised when there is an error with external API calls"""
    pass
