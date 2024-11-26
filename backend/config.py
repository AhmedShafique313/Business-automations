from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "AI Business Platform"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 9000
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Email Settings
    EMAIL_ENABLED: bool = False  # Set to True in production
    EMAIL_PROVIDER: str = "mock"  # Options: mock, mailjet, smtp
    EMAIL_FROM: str = "noreply@aibusiness.platform"
    EMAIL_FROM_NAME: str = "AI Business Platform"
    
    # Security Settings
    SECRET_KEY: str = "development_secret_key"  # Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database Settings (for future use)
    DATABASE_URL: str = "sqlite:///./test.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
