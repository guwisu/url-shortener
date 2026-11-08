from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from url_shortener.models import Link
from url_shortener.tasks.sync import sync_clicks_to_db


async def test_sync_clicks_to_db(db_session: AsyncSession, redis_client: Redis, user_1):
    short_code = "task123"
    link = Link(
        original_url="https://example.com",
        short_code=short_code,
        user_id=user_1.id,
        clicks_count=0,
    )
    db_session.add(link)
    await db_session.commit()

    await redis_client.set(f"clicks:{short_code}", "5")

    await sync_clicks_to_db(redis_client, db_session)

    await db_session.refresh(link)
    assert link.clicks_count == 5

    redis_clicks = await redis_client.get(f"clicks:{short_code}")
    assert redis_clicks is None
