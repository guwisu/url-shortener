import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from url_shortener.models import Link

log = logging.getLogger(__name__)


async def sync_clicks_to_db(redis: Redis, session: AsyncSession) -> None:
    async for key in redis.scan_iter(match="clicks:*"):
        short_code = key[7:]
        clicks_raw = await redis.getdel(key)
        if not clicks_raw:
            continue

        clicks = int(clicks_raw)

        try:
            query = (
                update(Link)
                .where(Link.short_code == short_code)
                .values(clicks_count=Link.clicks_count + clicks)
            )
            await session.execute(query)
            await session.commit()
        except Exception as e:  # noqa: BLE001
            await session.rollback()
            log.error(f"DB error syncing clicks for {short_code}: {e}")

            try:
                await redis.incrby(key, clicks)
            except RedisError as re:
                log.error(f"Failed to restore clicks to Redis for {short_code}: {re}")
