"""
Enhanced logging configuration for the agency.
"""
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

class AgencyLogger:
    def __init__(self, name: str, log_dir: Optional[str] = None):
        if log_dir is None:
            log_dir = str(Path(__file__).parents[4] / 'logs')
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Create handlers
        # Main log file
        main_handler = RotatingFileHandler(
            self.log_dir / f"{name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        main_handler.setLevel(logging.INFO)
        main_handler.setFormatter(file_formatter)
        
        # Error log file
        error_handler = RotatingFileHandler(
            self.log_dir / f"{name}_error.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Debug log file
        debug_handler = RotatingFileHandler(
            self.log_dir / f"{name}_debug.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(debug_handler)
        self.logger.addHandler(console_handler)
    
    def get_logger(self) -> logging.Logger:
        return self.logger
    
    @staticmethod
    def format_error(error: Exception) -> str:
        """Format exception information for logging."""
        return f"{type(error).__name__}: {str(error)}"
