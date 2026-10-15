from fastapi import APIRouter

from url_shortener.schemas.links import LinkCreate, LinkResponse

router = APIRouter(prefix="/links", tags=["links"])

@router.post("/", response_model=LinkResponse)
async def create_link(payload: LinkCreate):
    ...