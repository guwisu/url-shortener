import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from url_shortener.models import Link

log = logging.getLogger(__name__)


async def process_single_key(
    processing_key: str, redis: Redis, session: AsyncSession
) -> None:
    short_code = processing_key.split(":")[-1]

    clicks_raw = await redis.get(processing_key)
    if not clicks_raw:
        await redis.delete(processing_key)
        return

    clicks = int(clicks_raw)

    try:
        query = (
            update(Link)
            .where(Link.short_code == short_code)
            .values(clicks_count=Link.clicks_count + clicks)
        )
        await session.execute(query)
        await session.commit()

        await redis.delete(processing_key)

    except Exception as e:  # noqa: BLE001
        await session.rollback()
        log.error(f"DB error syncing clicks for {short_code}: {e}")


async def sync_clicks_to_db(redis: Redis, session: AsyncSession) -> None:
    async for processing_key in redis.scan_iter("processing:clicks:*"):
        await process_single_key(processing_key, redis, session)

    async for key in redis.scan_iter("clicks:*"):
        processing_key = f"processing:{key}"
        try:
            await redis.rename(key, processing_key)
        except RedisError:
            continue

        await process_single_key(processing_key, redis, session)
