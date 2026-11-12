import asyncio
import logging
import random

from url_shortener.tasks.celery_app import celery_app

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


async def _send_welcome_email_async(email: str):

    await asyncio.sleep(1)
    if random.choice([True, False]):
        raise ConnectionError("SMTP timeout")
    else:
        log.info("Email sent successfully")


@celery_app.task(bind=True, max_retries=3)
def send_welcome_email_task(self, email: str):
    try:
        asyncio.run(_send_welcome_email_async(email))
    except ConnectionError as e:
        pause = 5 * (2**self.request.retries)
        log.error(f"Error! Trying again in {pause} sec...")

        raise self.retry(exc=e, countdown=pause)
