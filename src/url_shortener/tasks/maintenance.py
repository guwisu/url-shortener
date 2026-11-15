import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select, update

from url_shortener.db.session import celery_session_factory
from url_shortener.models import Link
from url_shortener.tasks.celery_app import celery_app
from url_shortener.utils.security import check_url_is_alive

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


async def _deactivate_expired_links_async():
    async with celery_session_factory() as session:
        stmt = (
            update(Link)
            .where(Link.is_active.is_(True), Link.expires_at < datetime.now(UTC))
            .values(is_active=False)
        )
        await session.execute(stmt)
        await session.commit()


@celery_app.task(bind=True)
def deactivate_expired_links_task(self):
    log.info("Starting deactivate_expired_links task")
    asyncio.run(_deactivate_expired_links_async())


async def _check_url_is_alive_batch():
    async with celery_session_factory() as session:
        query = select(Link).where(Link.is_active.is_(True))
        result = await session.execute(query)
        links = list(result.scalars().all())
        if not links:
            return
        semaphore = asyncio.Semaphore(20)

        tasks = [check_url_is_alive(link.original_url, semaphore) for link in links]

        results = await asyncio.gather(*tasks)

        alive_ids = []
        dead_ids = []
        now = datetime.now(UTC)

        for link, is_alive in zip(links, results):
            if is_alive:
                alive_ids.append(link.id)
            else:
                dead_ids.append(link.id)

        if alive_ids:
            await session.execute(
                update(Link)
                .where(Link.id.in_(alive_ids))
                .values(is_alive=True, last_checked_at=now)
            )

        if dead_ids:
            await session.execute(
                update(Link)
                .where(Link.id.in_(dead_ids))
                .values(is_alive=False, last_checked_at=now)
            )

        await session.commit()


@celery_app.task(bind=True)
def check_url_is_alive_task(self):
    log.info("Starting check_url_is_alive_async task")
    asyncio.run(_check_url_is_alive_batch())
