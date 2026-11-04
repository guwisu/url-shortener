from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from url_shortener.core.security import decode_access_token
from url_shortener.db.session import get_db
from url_shortener.models import User
from url_shortener.repositories import LinkRepository
from url_shortener.repositories.users import UserRepository
from url_shortener.services import AuthService, LinkService
from url_shortener.services.cache import LinkCache


def get_link_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LinkRepository:
    return LinkRepository(session)


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_link_cache(redis: Annotated[Redis, Depends(get_redis)]) -> LinkCache:
    return LinkCache(redis)


def get_link_service(
    repository: Annotated[LinkRepository, Depends(get_link_repository)],
    cache: Annotated[LinkCache, Depends(get_link_cache)],
) -> LinkService:
    return LinkService(repository, cache)


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    return UserRepository(session)


def get_auth_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(repository)


oauth2_scheme = HTTPBearer()


async def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    decoded_token = decode_access_token(token.credentials)
    if decoded_token is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await repo.get_by_id(decoded_token)
    if not user:
        raise HTTPException(status_code=401)
    return user
