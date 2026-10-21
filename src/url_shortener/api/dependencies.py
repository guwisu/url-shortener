from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from url_shortener.db.session import get_db
from url_shortener.repositories import LinkRepository
from url_shortener.services import LinkService


def get_link_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LinkRepository:
    return LinkRepository(session)


def get_link_service(
    repository: Annotated[LinkRepository, Depends(get_link_repository)],
) -> LinkService:
    return LinkService(repository)
