import json
from pathlib import Path

import pytest
from django.db import IntegrityError

from tickets.choices import Category, HandoffReason
from tickets.models import AgentRun, Ticket

INTENT_MAP_PATH = Path(__file__).parents[2] / "evals" / "intent_map.json"


@pytest.fixture(scope="module")
def intent_map() -> dict:
    return json.loads(INTENT_MAP_PATH.read_text(encoding="utf-8"))


def test_categories_match_intent_map(intent_map):
    assert set(Category.values) == set(intent_map["categories"])


def test_evaluated_reasons_are_valid_hand_off_reasons(intent_map):
    assert set(intent_map["handoff_reasons"]) <= set(HandoffReason.values)


@pytest.fixture
def ticket(db) -> Ticket:
    return Ticket.objects.create(customer_id="c-0001", text="My card hasn't arrived yet")


def test_new_ticket_starts_as_received(ticket):
    assert ticket.status == Ticket.Status.RECEIVED


def test_valid_runs_are_saved(ticket):
    AgentRun.objects.create(
        ticket=ticket, outcome=AgentRun.Outcome.ANSWERED, answer="It takes 5–7 working days.", cited_articles=["kb-002"]
    )
    AgentRun.objects.create(
        ticket=ticket, outcome=AgentRun.Outcome.HANDED_OFF, handoff_reason=HandoffReason.LOW_CONFIDENCE
    )
    AgentRun.objects.create(ticket=ticket, outcome=AgentRun.Outcome.FAILED, error="Provider timeout")

    assert ticket.runs.count() == 3


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param({"outcome": "answered", "answer": ""}, id="answer-without-text"),
        pytest.param({"outcome": "answered", "answer": "Hi", "handoff_reason": "low_confidence"}, id="answer-with-reason"),
        pytest.param({"outcome": "handed_off"}, id="handoff-without-reason"),
        pytest.param({"outcome": "failed"}, id="failure-without-error"),
        pytest.param(
            {"outcome": "handed_off", "handoff_reason": "low_confidence", "confidence": 1.5}, id="confidence-above-1"
        ),
    ],
)
def test_invalid_runs_are_rejected_by_the_database(ticket, fields):
    with pytest.raises(IntegrityError):
        AgentRun.objects.create(ticket=ticket, **fields)
        