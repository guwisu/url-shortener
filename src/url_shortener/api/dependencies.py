from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from url_shortener.core.security import decode_access_token
from url_shortener.db.session import get_db
from url_shortener.models import User
from url_shortener.repositories import LinkRepository
from url_shortener.repositories.users import UserRepository
from url_shortener.services import AuthService, LinkService


def get_link_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LinkRepository:
    return LinkRepository(session)


def get_link_service(
    repository: Annotated[LinkRepository, Depends(get_link_repository)],
) -> LinkService:
    return LinkService(repository)


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
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    repo: UserRepository = Depends(get_user_repository),
) -> User:
    decoded_token = decode_access_token(token.credentials)
    if decoded_token is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await repo.get_by_id(decoded_token)
    if not user:
        raise HTTPException(status_code=401)
    return user