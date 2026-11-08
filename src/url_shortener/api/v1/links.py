from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from url_shortener.api.dependencies import (
    get_current_user,
    get_link_service,
)
from url_shortener.core.rate_limit import limiter
from url_shortener.models import User
from url_shortener.schemas.links import LinkCreate, LinkPublic, LinkResponse
from url_shortener.services import LinkService

router = APIRouter(prefix="/links", tags=["links"])

redirect_router = APIRouter(tags=["links"])


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_link(
    request: Request,
    body: LinkCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[LinkService, Depends(get_link_service)],
):
    return await service.create_link(current_user.id, str(body.url), body.expires_at)


@router.get("/{code}", response_model=LinkPublic)
async def get_by_code(
    code: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[LinkService, Depends(get_link_service)],
):
    link = await service.get_by_code(current_user.id, code)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link not found"
        )
    return link


@redirect_router.get("/{code}")
async def redirect_by_code(
    code: str,
    service: Annotated[LinkService, Depends(get_link_service)],
):
    link = await service.redirect_by_code(code)
    return RedirectResponse(
        url=link.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )


@router.get("")
async def get_all_by_user(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[LinkService, Depends(get_link_service)],
    skip: int = Query(0, ge=0, description="How much to skip"),
    limit: int = Query(20, ge=1, le=100, description="How much to return (max 100)"),
) -> list[LinkResponse]:
    return await service.get_all_by_user(current_user.id, skip, limit)


@router.delete("/{link_id}", response_model=LinkResponse)
async def delete_user_link(
    link_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[LinkService, Depends(get_link_service)],
) -> LinkResponse:
    return await service.delete_user_link(current_user.id, link_id)


@router.patch("/{link_id}/deactivate", response_model=LinkResponse)
async def deactivate_user_link(
    link_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[LinkService, Depends(get_link_service)],
) -> LinkResponse:
    return await service.set_active(current_user.id, link_id, value=False)


@router.patch("/{link_id}/activate", response_model=LinkResponse)
async def activate_user_link(
    link_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[LinkService, Depends(get_link_service)],
) -> LinkResponse:
    return await service.set_active(current_user.id, link_id, value=True)
