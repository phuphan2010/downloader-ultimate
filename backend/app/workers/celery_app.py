"""Celery Application configuration for distributed worker task queue."""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "downloader_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.DOWNLOAD_TIMEOUT_SEC + 60,
    task_default_queue="default",
)
