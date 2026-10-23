from collections.abc import AsyncGenerator

import pytest
from alembic import command
from alembic.config import Config
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


@pytest.fixture(scope="session", autouse=True)
def run_migrations_for_tests() -> None:
    alembic_cfg = Config("alembic.ini")

    alembic_cfg.set_main_option("sqlalchemy.url", settings.test_db_url)

    command.upgrade(alembic_cfg, "head")


test_engine = create_async_engine(settings.test_db_url, echo=False)
test_session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def clean_database() -> AsyncGenerator[None]:
    yield
    async with test_session_factory() as session:
        await session.execute(
            text("TRUNCATE TABLE links, users RESTART IDENTITY CASCADE;")
        )
        await session.commit()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    async with test_session_factory() as session:
        yield session


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
