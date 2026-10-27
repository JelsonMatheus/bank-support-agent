import logging
import time
from dataclasses import asdict
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from agent.types import Agent
from agent.registry import get_agent
from tickets.models import AgentRun, Ticket


logger = logging.getLogger(__name__)


FINAL_STATUS = {
    "answered": Ticket.Status.ANSWERED,
    "handed_off": Ticket.Status.HANDED_OFF,
}

MAX_ERROR_LENGTH = 2000


def enqueue_ticket(ticket_id: UUID) -> None:
    """Send a ticket to the queue. Never raises: a ticket that can't be queued
    stays 'received' and is picked up by `requeue_stale_tickets`."""
    from tickets.tasks import process_ticket_task

    try:
        process_ticket_task.delay(str(ticket_id))
    except Exception:
        logger.exception("Could not enqueue ticket %s", ticket_id)


def process_ticket(ticket_id: UUID | str, agent: Agent | None = None) -> AgentRun | None:
    """Run the agent on a ticket and store the result.

    Returns None if the ticket wasn't waiting to be processed, so running this
    twice for the same ticket is harmless.
    """
    claimed = Ticket.objects.filter(id=ticket_id, status=Ticket.Status.RECEIVED).update(
        status=Ticket.Status.PROCESSING, updated_at=timezone.now()
    )
    if not claimed:
        logger.info("Ticket %s is not waiting to be processed; skipping", ticket_id)
        return None

    ticket = Ticket.objects.get(id=ticket_id)
    agent = agent or get_agent()
    started = time.perf_counter()

    try:
        result = agent.run(ticket.text, customer_id=ticket.customer_id)
        status = FINAL_STATUS[result.outcome]
        with transaction.atomic():
            run = AgentRun.objects.create(ticket=ticket, latency_ms=_elapsed_ms(started), **asdict(result))
            _set_status(ticket, status)
        return run
    except Exception as exc:
        logger.exception("Processing failed for ticket %s", ticket_id)
        with transaction.atomic():
            run = AgentRun.objects.create(
                ticket=ticket,
                outcome=AgentRun.Outcome.FAILED,
                error=repr(exc)[:MAX_ERROR_LENGTH],
                latency_ms=_elapsed_ms(started),
            )
            _set_status(ticket, Ticket.Status.FAILED)
        return run


def _set_status(ticket: Ticket, status: str) -> None:
    Ticket.objects.filter(id=ticket.id).update(status=status, updated_at=timezone.now())


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
