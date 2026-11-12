import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import update

from url_shortener.db.session import celery_session_factory
from url_shortener.models import Link
from url_shortener.tasks.celery_app import celery_app

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
