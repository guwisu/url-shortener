from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from url_shortener.api.dependencies import get_link_service
from url_shortener.schemas.links import LinkCreate, LinkResponse
from url_shortener.services import LinkService

router = APIRouter(prefix="/links", tags=["links"])

redirect_router = APIRouter(tags=["links"])

@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    payload: LinkCreate,
    service: Annotated[LinkService, Depends(get_link_service)]
):
    return await service.create_link(str(payload.url), payload.expires_at)

@router.get("/{code}", response_model=LinkResponse)
async def get_by_code(
    code: str,
    service: Annotated[LinkService, Depends(get_link_service)]
):
    link = await service.get_by_code(code)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return link
    
@redirect_router.get("/{code}")
async def redirect_by_code(
    code: str,
    service: Annotated[LinkService, Depends(get_link_service)]
):
    link_data = await service.get_and_increment_clicks(code)
    if not link_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return RedirectResponse(url=link_data.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)