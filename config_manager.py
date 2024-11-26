"""Configuration management module for Design Gaga automation system.

This module provides a singleton configuration manager that handles loading,
saving, and accessing configuration settings from both files and environment
variables. It supports JSON-based configuration with environment variable
overrides and includes JSON logging capabilities.

Typical usage:
    config = ConfigManager()
    api_key = config.get('api', 'openai', 'key')
    config.set('company', 'name', value='New Company Name')
    config.save()
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, TypeVar, cast
import logging
from pythonjsonlogger import jsonlogger

T = TypeVar('T')

class ConfigManager:
    """Singleton configuration manager for the Design Gaga automation system.
    
    This class manages all configuration settings, providing a centralized way to
    access and modify configuration values. It implements the Singleton pattern
    to ensure only one configuration instance exists across the application.
    
    Attributes:
        config (Dict[str, Any]): The current configuration dictionary
        logger (logging.Logger): JSON-formatted logger for the config manager
    """
    
    _instance: Optional['ConfigManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'ConfigManager':
        """Create or return the singleton instance of ConfigManager.
        
        Returns:
            ConfigManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the configuration manager if not already initialized."""
        if self._initialized:
            return
            
        self.setup_logging()
        self.load_config()
        self._initialized = True
    
    def setup_logging(self) -> None:
        """Set up JSON-formatted logging for the configuration manager.
        
        Configures a StreamHandler with JSON formatting for structured logging
        of configuration-related events and errors.
        """
        logHandler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            timestamp=True
        )
        logHandler.setFormatter(formatter)
        self.logger = logging.getLogger('ConfigManager')
        self.logger.addHandler(logHandler)
        self.logger.setLevel(logging.INFO)
    
    def load_config(self) -> None:
        """Load configuration from file with environment variable overrides.
        
        Attempts to load configuration from the default config file. If the file
        doesn't exist, creates it with default values. After loading, applies
        any environment variable overrides.
        
        Raises:
            OSError: If there are file system related errors
            json.JSONDecodeError: If the config file contains invalid JSON
        """
        try:
            config_path = Path('config/default_config.json')
            if not config_path.exists():
                self.logger.warning("Default config not found, creating one")
                self._create_default_config()
            
            with open(config_path) as f:
                self.config = json.load(f)
            
            self._apply_env_overrides()
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            self.config = self._get_default_config()
    
    def _create_default_config(self) -> None:
        """Create the default configuration file.
        
        Creates the config directory if it doesn't exist and writes the default
        configuration to a JSON file.
        
        Raises:
            OSError: If unable to create directory or write file
            json.JSONEncodeError: If unable to serialize config to JSON
        """
        config = self._get_default_config()
        os.makedirs('config', exist_ok=True)
        
        with open('config/default_config.json', 'w') as f:
            json.dump(config, f, indent=4)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get the default configuration dictionary.
        
        Returns:
            Dict[str, Any]: Default configuration values
        """
        return {
            "company": {
                "name": "Design Gaga",
                "website": "https://designgaga.com",
                "phone": "",
                "business_type": "design",
                "location": "Toronto"
            },
            "api": {
                "openai": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "rate_limit": {
                        "calls_per_minute": 50
                    }
                },
                "asana": {
                    "rate_limit": {
                        "calls_per_minute": 50
                    },
                    "retry": {
                        "max_attempts": 3,
                        "min_wait": 4,
                        "max_wait": 10
                    }
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                "handlers": ["file", "console"]
            }
        }
    
    def _apply_env_overrides(self) -> None:
        """Override configuration with environment variables.
        
        Maps environment variables to their corresponding configuration paths
        and updates the config values if environment variables are set.
        """
        env_mappings = {
            'COMPANY_NAME': ('company', 'name'),
            'COMPANY_WEBSITE': ('company', 'website'),
            'COMPANY_PHONE': ('company', 'phone'),
            'BUSINESS_TYPE': ('company', 'business_type'),
            'BUSINESS_LOCATION': ('company', 'location'),
            'OPENAI_MODEL': ('api', 'openai', 'model'),
            'LOG_LEVEL': ('logging', 'level')
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(self.config, config_path, value)
    
    def _set_nested_value(self, d: Dict[str, Any], path: Union[tuple[str, ...], List[str]], value: Any) -> None:
        """Set a value in a nested dictionary using a path tuple.
        
        Args:
            d: The dictionary to modify
            path: Tuple of keys representing the path to the value
            value: The value to set
            
        Raises:
            KeyError: If intermediate keys don't exist and can't be created
            TypeError: If intermediate keys exist but aren't dictionaries
        """
        for key in path[:-1]:
            d = d.setdefault(key, {})
        d[path[-1]] = value
    
    def get(self, *path: str, default: T = None) -> Union[Any, T]:
        """Get a configuration value using a path.
        
        Args:
            *path: Variable length path to the configuration value
            default: Value to return if path doesn't exist
            
        Returns:
            The configuration value at the specified path, or the default value
        """
        try:
            result = self.config
            for key in path:
                result = result[key]
            return result
        except (KeyError, TypeError):
            return default
    
    def set(self, *path: str, value: Any) -> None:
        """Set a configuration value using a path.
        
        Args:
            *path: Variable length path to the configuration value
            value: The value to set at the specified path
            
        Raises:
            KeyError: If intermediate keys don't exist and can't be created
            TypeError: If intermediate keys exist but aren't dictionaries
        """
        self._set_nested_value(self.config, path, value)
        
    def save(self) -> None:
        """Save current configuration to file.
        
        Raises:
            OSError: If unable to write to the config file
            json.JSONEncodeError: If unable to serialize config to JSON
        """
        try:
            with open('config/default_config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            raise
