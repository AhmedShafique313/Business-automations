from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
import redis
from aio_pika import connect_robust
import logging
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# PostgreSQL Configuration
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB Configuration
mongodb_client = AsyncIOMotorClient(
    f"mongodb://{settings.MONGODB_USER}:{settings.MONGODB_PASSWORD}@{settings.MONGODB_HOST}:{settings.MONGODB_PORT}"
)
mongodb = mongodb_client[settings.MONGODB_DB]

# Redis Configuration
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

# RabbitMQ Configuration
async def get_rabbitmq_connection():
    try:
        connection = await connect_robust(
            f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
        )
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
        raise

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize databases
async def init_db():
    try:
        # Create PostgreSQL tables
        Base.metadata.create_all(bind=engine)
        logger.info("PostgreSQL tables created successfully")

        # Test MongoDB connection
        await mongodb.command("ping")
        logger.info("MongoDB connection successful")

        # Test Redis connection
        redis_client.ping()
        logger.info("Redis connection successful")

        # Test RabbitMQ connection
        connection = await get_rabbitmq_connection()
        await connection.close()
        logger.info("RabbitMQ connection successful")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
