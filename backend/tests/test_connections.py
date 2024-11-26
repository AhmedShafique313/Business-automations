import asyncio
import asyncpg
import motor.motor_asyncio
import aioredis
import aio_pika
import pytest
from app.core.config import settings

@pytest.mark.asyncio
async def test_postgres_connection():
    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB
        )
        await conn.execute('SELECT 1')  # Simple query to test connection
        await conn.close()
        print("✅ PostgreSQL connection successful")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        return False

@pytest.mark.asyncio
async def test_mongodb_connection():
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(
            f"mongodb://{settings.MONGODB_USER}:{settings.MONGODB_PASSWORD}@{settings.MONGODB_HOST}:{settings.MONGODB_PORT}"
        )
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        return False

@pytest.mark.asyncio
async def test_redis_connection():
    try:
        redis = await aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        )
        await redis.ping()
        await redis.close()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        return False

@pytest.mark.asyncio
async def test_rabbitmq_connection():
    try:
        connection = await aio_pika.connect_robust(
            f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
        )
        await connection.close()
        print("✅ RabbitMQ connection successful")
        return True
    except Exception as e:
        print(f"❌ RabbitMQ connection failed: {str(e)}")
        return False

async def main():
    print("\nTesting all connections...")
    print("-" * 30)
    
    results = await asyncio.gather(
        test_postgres_connection(),
        test_mongodb_connection(),
        test_redis_connection(),
        test_rabbitmq_connection()
    )
    
    print("-" * 30)
    if all(results):
        print("✨ All connections successful!")
    else:
        print("⚠️  Some connections failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
