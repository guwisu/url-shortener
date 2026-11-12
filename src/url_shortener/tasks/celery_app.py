from celery import Celery

from url_shortener.core.config import settings

celery_app = Celery("url_shortener", broker=settings.CELERY_BROKER_URL)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.imports = [
    "url_shortener.tasks.emails",
    "url_shortener.tasks.maintenance",
]

celery_app.conf.beat_schedule = {
    "deactivate_expired_links": {
        "task": "url_shortener.tasks.maintenance.deactivate_expired_links_async",
        "schedule": 15.0,
    }
}
