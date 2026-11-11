import asyncio
import logging
import signal
import sys

from redis.asyncio import Redis

from url_shortener.core.config import settings
from url_shortener.db.session import async_session_factory
from url_shortener.tasks.sync import sync_clicks_to_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def click_sync_worker(redis_client: Redis, stop_event: asyncio.Event):
    log.info("Starting click sync worker...")

    while not stop_event.is_set():
        async with async_session_factory() as session:
            try:
                await sync_clicks_to_db(redis_client, session)
            except Exception as e:  # noqa: BLE001
                log.error(f"Redis error: {e}")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=30.0)
        except TimeoutError:
            pass


async def main():
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    if sys.platform != "win32":
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, stop_event.set)
    else:
        pass
    redis_client = Redis.from_url(url=settings.redis_url, decode_responses=True)
    try:
        await click_sync_worker(redis_client, stop_event)
    except KeyboardInterrupt:
        log.info("Received KeyboardInterrupt (Windows)")
        stop_event.set()
    finally:
        log.info("Worker shutting down gracefully...")
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
