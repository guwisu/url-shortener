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
from sqlalchemy.pool import NullPool

from url_shortener.core.config import settings
from url_shortener.core.security import create_access_token, hash_password
from url_shortener.db.session import get_db
from url_shortener.main import app
from url_shortener.models import User


@pytest.fixture(scope="session", autouse=True)
def run_migrations_for_tests() -> None:
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.test_db_url)
    command.upgrade(alembic_cfg, "head")


test_engine = create_async_engine(settings.test_db_url, echo=False, poolclass=NullPool)
test_session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def clean_database():
    yield
    async with test_session_factory() as session:
        await session.execute(
            text("TRUNCATE TABLE links, users RESTART IDENTITY CASCADE;")
        )
        await session.commit()


@pytest.fixture
async def db_session():
    async with test_session_factory() as session:
        yield session


@pytest.fixture(autouse=True)
async def override_get_db(db_session: AsyncSession):
    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session: AsyncSession):
    async def _make_user(
        email: str = "test@example.com",
        password: str = "test_password123",
    ) -> User:
        user = User(email=email, hashed_password=hash_password(password))
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def make_client():
    def _make_client(user: User | None = None) -> AsyncClient:
        headers = {}
        if user is not None:
            headers["Authorization"] = f"Bearer {create_access_token(user.id)}"
        return AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=headers,
        )

    return _make_client


@pytest.fixture
async def user_1(make_user) -> User:
    return await make_user("test1@example.com")


@pytest.fixture
async def user_2(make_user) -> User:
    return await make_user("test2@example.com")


@pytest.fixture
async def client(make_client):
    async with make_client() as c:
        yield c


@pytest.fixture
async def auth_client_1(make_client, user_1: User):
    async with make_client(user_1) as c:
        yield c


@pytest.fixture
async def auth_client_2(make_client, user_2: User):
    async with make_client(user_2) as c:
        yield c
