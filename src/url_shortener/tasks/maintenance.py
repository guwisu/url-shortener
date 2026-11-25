import asyncio
import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy import select, update

from url_shortener.db.session import celery_session_factory
from url_shortener.models import Link
from url_shortener.tasks.celery_app import celery_app
from url_shortener.utils.security import check_url_is_alive

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


async def _check_url_is_alive_batch(batch_size: int = 100) -> None:
    semaphore = asyncio.Semaphore(20)
    last_id = 0

    async with httpx.AsyncClient(
        timeout=5.0,
        headers={
            "User-Agent": "url-shortener-bot/1.0 (+https://github.com/guwisu/url-shortener)"
        },
    ) as client:
        while True:
            async with celery_session_factory() as session:
                query = (
                    select(Link.id, Link.original_url)
                    .where(Link.is_active.is_(True), Link.id > last_id)
                    .order_by(Link.id.asc())
                    .limit(batch_size)
                )
                result = await session.execute(query)
                batch = result.all()

            if not batch:
                break

            last_id = batch[-1].id
            tasks = [
                check_url_is_alive(row.original_url, semaphore, client) for row in batch
            ]
            results = await asyncio.gather(*tasks)

            alive_ids = [row.id for row, alive in zip(batch, results) if alive]
            dead_ids = [row.id for row, alive in zip(batch, results) if not alive]
            now = datetime.now(UTC)

            async with celery_session_factory() as session:
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
