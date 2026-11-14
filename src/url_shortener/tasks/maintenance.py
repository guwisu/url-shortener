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
def deactivate_expired_links_async(self):
    log.info("Starting deactivate_expired_links task")
    asyncio.run(_deactivate_expired_links_async())
    log.info("Completed deactivate_expired_links task")


async def _check_url_is_alive_async():
    async with celery_session_factory() as session:
        query = select(Link).where(Link.is_active.is_(True))
        result = await session.execute(query)
        links = list(result.scalars().all())
        if not links:
            return

        all_ids = {link.id for link in links}
        need_ids = set()

        for link in links:
            if not await check_url_is_alive(link.original_url):
                need_ids.add(link.id)

        if need_ids:
            alive_stmt = (
                update(Link).where(Link.id.in_(need_ids)).values(is_alive=False)
            )
            await session.execute(alive_stmt)

        checked_stmt = (
            update(Link)
            .where(Link.id.in_(all_ids))
            .values(last_checked_at=datetime.now(UTC))
        )
        await session.execute(checked_stmt)
        await session.commit()


@celery_app.task(bind=True)
def check_url_is_alive_async(self):
    log.info("Starting check_url_is_alive_async task")
    asyncio.run(_check_url_is_alive_async())
    log.info("Completed check_url_is_alive_async task")
