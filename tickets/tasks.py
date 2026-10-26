import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def ping() -> str:
    """Smoke test for the queue: proves a message goes from Django to a worker."""
    logger.info("pong")
    return "pong"