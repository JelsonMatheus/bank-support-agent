import logging

from celery import shared_task
from tickets.services import process_ticket


logger = logging.getLogger(__name__)


@shared_task
def ping() -> str:
    """Smoke test for the queue: proves a message goes from Django to a worker."""
    logger.info("pong")
    return "pong"


@shared_task
def process_ticket_task(ticket_id: str) -> None:
    process_ticket(ticket_id)