from celery import Celery
from config import get_settings

settings = get_settings()

celery_app = Celery(
    "openseo",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["tasks.crawler", "tasks.competitive", "tools.content_optimizer", "tools.bulk_url_analyzer"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
)
