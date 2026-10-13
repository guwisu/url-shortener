from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from url_shortener.core.config import settings

async_engine = create_async_engine(
    url=settings.db_url,
    echo=False,
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False
)


async def get_db():
    async with async_session_factory() as session:
        yield session