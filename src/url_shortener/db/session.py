from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from url_shortener.core.config import settings

async_engine = create_async_engine(
    settings.db_url,
    echo=False,
)
async_session_factory = async_sessionmaker(bind=async_engine, expire_on_commit=False)

celery_engine = create_async_engine(settings.db_url, poolclass=NullPool)
celery_session_factory = async_sessionmaker(celery_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
