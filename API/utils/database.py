from os import getenv
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker,AsyncEngine

engine: AsyncEngine = create_async_engine(
    #Todo Изменить на env, плдключение к db
    f"postgresql+asyncpg://spectral:spectral@localhost:5432/spectral",
    echo=True, #Todo удалить
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