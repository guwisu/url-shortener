from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_db(session: AsyncSession) -> int:
    result = await session.execute(text("SELECT 1"))
    return result.scalar_one()
