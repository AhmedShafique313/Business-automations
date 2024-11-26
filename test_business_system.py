"""Test suite for Design Gaga automation system.

This module contains comprehensive tests for the core components of the
Design Gaga automation system, including configuration management,
business generation, AI integration, and task execution.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Generator, Any

from business_generator import BusinessGenerator, OPTIONAL_DEPS
from config_manager import ConfigManager
from ai_agent import AIAgent
from task_executor import TaskExecutor

@pytest.fixture
def clean_config() -> None:
    """Reset configuration to defaults before each test."""
    # Reset singleton state
    ConfigManager._instance = None
    ConfigManager._initialized = False
    
    # Clean up any existing config file
    try:
        os.remove('config/default_config.json')
    except FileNotFoundError:
        pass
    
    # Ensure config directory exists
    os.makedirs('config', exist_ok=True)

@pytest.fixture
def config_manager(clean_config) -> Generator[ConfigManager, None, None]:
    """Fixture that provides a clean ConfigManager instance for each test."""
    # Create instance
    manager = ConfigManager()
    yield manager

@pytest.fixture
def mock_asana() -> Generator[MagicMock, None, None]:
    """Fixture that provides a mocked Asana client."""
    with patch('asana.Client') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.tags.get_tags.return_value = []
        yield mock_instance

def test_config_manager_singleton(config_manager: ConfigManager) -> None:
    """Test that ConfigManager properly implements the singleton pattern."""
    config1 = ConfigManager()
    config2 = ConfigManager()
    assert config1 is config2
    assert config1 is config_manager

def test_config_manager_default_values(config_manager: ConfigManager) -> None:
    """Test that ConfigManager provides correct default values."""
    assert config_manager.get('company', 'name') == 'Design Gaga'
    assert config_manager.get('api', 'openai', 'model') == 'gpt-4'
    assert config_manager.get('nonexistent', default='default') == 'default'

def test_config_manager_set_get(config_manager: ConfigManager) -> None:
    """Test setting and getting configuration values."""
    # Test simple set/get
    config_manager.set('company', 'name', value='Test Company')
    assert config_manager.get('company', 'name') == 'Test Company'
    
    # Test nested set/get
    config_manager.set('api', 'custom', 'key', value='test-key')
    assert config_manager.get('api', 'custom', 'key') == 'test-key'
    
    # Test default values
    assert config_manager.get('nonexistent', 'path', default=None) is None
    assert config_manager.get('nonexistent', 'path', default='default') == 'default'

def test_config_manager_env_override(config_manager: ConfigManager) -> None:
    """Test environment variable overrides."""
    # Set environment variables
    os.environ['COMPANY_NAME'] = 'Env Company'
    os.environ['BUSINESS_TYPE'] = 'tech'
    
    # Reload config
    config_manager.load_config()
    
    # Check overrides
    assert config_manager.get('company', 'name') == 'Env Company'
    assert config_manager.get('company', 'business_type') == 'tech'
    
    # Clean up
    del os.environ['COMPANY_NAME']
    del os.environ['BUSINESS_TYPE']

def test_config_manager_save_load(config_manager: ConfigManager) -> None:
    """Test saving and loading configuration."""
    # Make changes
    config_manager.set('company', 'name', value='Test Company')
    config_manager.set('api', 'custom', 'key', value='test-key')
    
    # Save config
    config_manager.save()
    
    # Create new instance (should load from file)
    ConfigManager._instance = None
    new_config = ConfigManager()
    
    # Verify changes persisted
    assert new_config.get('company', 'name') == 'Test Company'
    assert new_config.get('api', 'custom', 'key') == 'test-key'

@pytest.mark.usefixtures("clean_config")
def test_business_generator_initialization() -> None:
    """Test BusinessGenerator initialization and feature detection."""
    generator = BusinessGenerator()
    
    # Test company details
    assert generator.company_name == 'Design Gaga' or os.getenv('COMPANY_NAME')
    assert generator.business_type == 'design' or os.getenv('BUSINESS_TYPE')
    
    # Test template loading
    assert generator.templates is not None
    assert 'follow_up_email' in generator.templates
    assert 'cold_call' in generator.templates
    
    # Test optional features
    assert isinstance(OPTIONAL_DEPS, dict)
    for feature in ['twilio', 'google', 'selenium', 'speech']:
        assert feature in OPTIONAL_DEPS

@pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="OpenAI API key not set")
def test_ai_agent_integration() -> None:
    """Test AI agent integration with OpenAI."""
    agent = AIAgent()
    response = agent.get_completion("Hello, how are you?")
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_task_executor_initialization(mock_asana: MagicMock) -> None:
    """Test TaskExecutor initialization and Asana integration."""
    executor = TaskExecutor()
    
    # Test Asana integration
    if os.getenv('ASANA_ACCESS_TOKEN'):
        # Verify tag setup was called
        assert mock_asana.tags.get_tags.called
        
        # Test task execution
        result = executor._execute_task("monitor_listings")
        assert isinstance(result, list)

def test_task_executor_error_handling(mock_asana: MagicMock) -> None:
    """Test TaskExecutor error handling."""
    # Make Asana client raise an error
    mock_asana.tags.get_tags.side_effect = Exception("Asana API error")
    
    executor = TaskExecutor()
    
    # Should handle the error gracefully
    if os.getenv('ASANA_ACCESS_TOKEN'):
        result = executor._execute_task("monitor_listings")
        assert isinstance(result, list)
        assert len(result) == 0

if __name__ == "__main__":
    # Set up test environment
    os.environ['ENVIRONMENT'] = 'test'
    
    # Run tests
    pytest.main([__file__, '-v'])
