from fastapi import APIRouter

from url_shortener.db.health import check_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    await check_db()
    return {"status": "OK"}
