import uuid

import pytest
from django.urls import reverse

from agent.baseline import BaselineAgent
from agent.types import AgentResult
from tickets.models import AgentRun, Ticket
from tickets.services import process_ticket

pytestmark = pytest.mark.django_db


class AnsweringAgent:
    def run(self, text: str, customer_id: str) -> AgentResult:
        return AgentResult(
            outcome="answered", category="cards", confidence=0.9,
            answer="Cards arrive 5–7 working days after dispatch.", cited_articles=["kb-002"],
        )


class FailingAgent:
    def run(self, text: str, customer_id: str) -> AgentResult:
        raise RuntimeError("provider timeout")


class InvalidResultAgent:
    def run(self, text: str, customer_id: str) -> AgentResult:
        return AgentResult(outcome="handed_off")  # a hand-off without a reason


class UnknownOutcomeAgent:
    def run(self, text: str, customer_id: str) -> AgentResult:
        return AgentResult(outcome="maybe")


@pytest.fixture
def ticket() -> Ticket:
    return Ticket.objects.create(customer_id="c-0001", text="My card hasn't arrived")


def test_baseline_hands_every_ticket_off(ticket):
    run = process_ticket(ticket.id, agent=BaselineAgent())

    ticket.refresh_from_db()
    assert ticket.status == Ticket.Status.HANDED_OFF
    assert run.outcome == AgentRun.Outcome.HANDED_OFF
    assert run.handoff_reason == "low_confidence"


def test_answer_marks_ticket_answered(ticket):
    run = process_ticket(ticket.id, agent=AnsweringAgent())

    ticket.refresh_from_db()
    assert ticket.status == Ticket.Status.ANSWERED
    assert run.cited_articles == ["kb-002"]


def test_processing_twice_creates_a_single_run(ticket):
    process_ticket(ticket.id, agent=BaselineAgent())
    second = process_ticket(ticket.id, agent=BaselineAgent())

    assert second is None
    assert ticket.runs.count() == 1


@pytest.mark.parametrize(
    "agent",
    [FailingAgent(), InvalidResultAgent(), UnknownOutcomeAgent()],
    ids=["agent-raises", "invalid-result", "unknown-outcome"],
)
def test_failures_are_recorded_and_never_leave_ticket_processing(ticket, agent):
    run = process_ticket(ticket.id, agent=agent)

    ticket.refresh_from_db()
    assert ticket.status == Ticket.Status.FAILED
    assert run.outcome == AgentRun.Outcome.FAILED
    assert run.error
    assert ticket.runs.count() == 1


def test_creating_a_ticket_enqueues_it_after_commit(client, monkeypatch, django_capture_on_commit_callbacks):
    enqueued = []
    monkeypatch.setattr("tickets.views.enqueue_ticket", enqueued.append)

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            reverse("tickets:create"),
            {"customer_id": "c-0001", "text": "My card hasn't arrived"},
            content_type="application/json",
        )

    assert enqueued == [uuid.UUID(response.json()["id"])]