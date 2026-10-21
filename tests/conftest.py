from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from url_shortener.core.config import settings
from url_shortener.db.session import get_db
from url_shortener.main import app


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine(settings.db_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        await session.execute(text("TRUNCATE TABLE links RESTART IDENTITY CASCADE;"))
        await session.commit()

    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
