import uuid

import pytest
from django.urls import reverse

from tickets.choices import HandoffReason
from tickets.models import AgentRun, Ticket
from tickets.serializers import MAX_TEXT_LENGTH

pytestmark = pytest.mark.django_db

CREATE_URL = reverse("tickets:create")


def post_ticket(client, payload: dict):
    return client.post(CREATE_URL, payload, content_type="application/json")


def test_create_ticket_returns_202_with_location(client):
    response = post_ticket(client, {"customer_id": "c-0001", "text": "My card hasn't arrived"})

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "received"
    assert body["channel"] == "chat"
    assert body["result"] is None
    assert response["Location"] == reverse("tickets:detail", kwargs={"id": body["id"]})
    assert Ticket.objects.filter(id=body["id"]).exists()


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        pytest.param({"customer_id": "c-0001"}, "text", id="missing-text"),
        pytest.param({"customer_id": "c-0001", "text": "   "}, "text", id="blank-text"),
        pytest.param({"customer_id": "c-0001", "text": "x" * (MAX_TEXT_LENGTH + 1)}, "text", id="text-too-long"),
        pytest.param({"text": "Hello"}, "customer_id", id="missing-customer"),
        pytest.param({"customer_id": "c-0001", "text": "Hello", "channel": "fax"}, "channel", id="unknown-channel"),
    ],
)
def test_create_ticket_rejects_invalid_input(client, payload, field):
    response = post_ticket(client, payload)

    assert response.status_code == 400
    assert field in response.json()
    assert Ticket.objects.count() == 0


def test_client_cannot_set_status(client):
    response = post_ticket(client, {"customer_id": "c-0001", "text": "Hello", "status": "answered"})

    assert response.status_code == 202
    assert response.json()["status"] == "received"


def test_retrieve_ticket_shows_latest_run(client):
    ticket = Ticket.objects.create(customer_id="c-0001", text="My card hasn't arrived")
    AgentRun.objects.create(ticket=ticket, outcome="handed_off", handoff_reason=HandoffReason.LOW_CONFIDENCE)
    AgentRun.objects.create(ticket=ticket, outcome="answered", answer="It takes 5–7 working days.", cited_articles=["kb-002"])

    response = client.get(reverse("tickets:detail", kwargs={"id": ticket.id}))

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["outcome"] == "answered"
    assert result["cited_articles"] == ["kb-002"]
    assert "input_tokens" not in result


def test_retrieve_unknown_ticket_returns_404(client):
    response = client.get(reverse("tickets:detail", kwargs={"id": uuid.uuid4()}))

    assert response.status_code == 404