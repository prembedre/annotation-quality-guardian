"""
Celery application configuration and initialization.
Uses Redis as message broker and result backend.
"""

from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "annotation_quality_guardian",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=[
        "app.tasks.behavioral_tasks",
        "app.tasks.embedding_tasks",
        "app.tasks.trust_score_tasks",
    ],
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    result_expires=86400,  # 24 hours
    broker_connection_retry_on_startup=True,
)


@celery_app.task(name="app.tasks.ping")
def ping_task() -> str:
    """Simple verification task to test worker connectivity."""
    return "pong"
