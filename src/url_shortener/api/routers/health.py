from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from url_shortener.db.health import check_db
from url_shortener.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(session: Annotated[AsyncSession, Depends(get_db)]):
    await check_db(session)
    return {"status": "OK"}
