from sqlalchemy import text

from url_shortener.db.session import async_engine


async def check_db():
    async with async_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        return result.scalar_one()
