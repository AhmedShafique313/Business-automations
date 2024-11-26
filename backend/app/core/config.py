from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Business AI Platform"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000"]  # Frontend URL
    
    # PostgreSQL settings
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "adminpassword"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5433"  # Updated port
    POSTGRES_DB: str = "business_automation"
    
    # MongoDB settings
    MONGODB_USER: str = "admin"
    MONGODB_PASSWORD: str = "adminpassword"
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: str = "27017"
    MONGODB_DB: str = "business_automation"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    
    # RabbitMQ settings
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASSWORD: str = "adminpassword"
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: str = "5672"
    
    # External API settings
    ASANA_ACCESS_TOKEN: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    SENDGRID_API_KEY: str = ""
    CLEARBIT_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    class Config:
        case_sensitive = True

settings = Settings()
