from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from url_shortener.api.dependencies import get_link_service
from url_shortener.schemas.links import LinkCreate, LinkResponse
from url_shortener.services import LinkService

router = APIRouter(prefix="/links", tags=["links"])

redirect_router = APIRouter(tags=["links"])

@router.post("", response_model=LinkResponse)
async def create_link(
    payload: LinkCreate,
    service: Annotated[LinkService, Depends(get_link_service)]
):
    return await service.create_link(str(payload.url))

@router.get("/{code}", response_model=LinkResponse)
async def get_by_code(
    code: str,
    service: Annotated[LinkService, Depends(get_link_service)]
):
    return await service.get_by_code(code)

@redirect_router.get("/{code}")
async def redirect_by_code(
    code: str,
    service: Annotated[LinkService, Depends(get_link_service)]
):
    link_data = await service.get_by_code(code)

    return RedirectResponse(url=link_data.original_url, status_code=307)