import asyncio

from sqlalchemy import text

from url_shortener.db.session import async_engine


async def main() -> None:
    async with async_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print(result.scalar_one())

    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())