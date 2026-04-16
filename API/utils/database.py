from os import getenv
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker,AsyncEngine

engine: AsyncEngine = create_async_engine(
    f"postgresql+asyncpg://{getenv("DB_USER")}:{getenv("DB_PASSWORD")}@db:5432/{getenv("DB_NAME")}",
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()