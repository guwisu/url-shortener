import asyncio
import logging

from redis.asyncio import Redis

from url_shortener.core.config import settings
from url_shortener.db.session import async_session_factory
from url_shortener.tasks.sync import sync_clicks_to_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def click_sync_worker(redis_client: Redis):
    log.info("Starting click sync worker...")
    while True:
        await asyncio.sleep(30)

        async with async_session_factory() as session:
            try:
                await sync_clicks_to_db(redis_client, session)
            except Exception as e:  # noqa: BLE001
                log.error(f"Redis error: {e}")


async def main():
    redis_client = Redis.from_url(url=settings.redis_url, decode_responses=True)
    try:
        await click_sync_worker(redis_client)
    except asyncio.CancelledError:
        log.info("Worker cancelled, shutting down...")
    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
