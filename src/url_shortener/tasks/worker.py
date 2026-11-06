import asyncio
import logging

from redis.asyncio import Redis

from url_shortener.db.session import async_session_factory
from url_shortener.tasks.sync import sync_clicks_to_db

log = logging.getLogger(__name__)


async def click_sync_worker(redis_client: Redis):
    while True:
        await asyncio.sleep(30)

        async with async_session_factory() as session:
            try:
                await sync_clicks_to_db(redis_client, session)
            except Exception as e:  # noqa: BLE001
                log.error(f"Redis error: {e}")
