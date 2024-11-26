"""Error handling utility for the business development system."""

import logging
import traceback
from typing import Optional, Any, Dict
from functools import wraps
from prometheus_client import Counter

# Prometheus metrics
ERROR_COUNTER = Counter('error_total', 'Total number of errors', ['type', 'component'])

def handle_error(error: Exception, component: str, context: Optional[Dict] = None) -> None:
    """Handle errors with logging and metrics tracking."""
    logger = logging.getLogger(component)
    
    # Track error in Prometheus
    error_type = type(error).__name__
    ERROR_COUNTER.labels(type=error_type, component=component).inc()
    
    # Log error with context
    error_message = f"Error in {component}: {str(error)}"
    if context:
        error_message += f"\nContext: {context}"
    
    logger.error(error_message)
    logger.debug(f"Traceback: {''.join(traceback.format_tb(error.__traceback__))}")
    
def error_boundary(component: str):
    """Decorator to add error handling to functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {
                    'args': args,
                    'kwargs': kwargs
                }
                handle_error(e, component, context)
                raise
        return wrapper
    return decorator
