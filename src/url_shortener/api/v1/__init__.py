from fastapi import APIRouter

from url_shortener.api.v1.links import router as links_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(links_router)