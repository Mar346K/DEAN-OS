import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

# Pull the credentials from the docker-compose environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://deanos_admin:deanos_vault_2026@db/deanos_history"
)

# Initialize the async engine
# 'pool_size' and 'max_overflow' ensure we don't drop connections during heavy swarm bursts
engine = create_async_engine(
    DATABASE_URL,
    echo=False, # Set to True if you want to see the raw SQL in your docker logs
    pool_size=10,
    max_overflow=20
)

# Create a session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI endpoints to get a DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
