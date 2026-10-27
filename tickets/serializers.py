from rest_framework import serializers

from tickets.models import AgentRun, Ticket

MAX_TEXT_LENGTH = 5000


class TicketCreateSerializer(serializers.ModelSerializer):
    """What a client may send when creating a ticket."""

    text = serializers.CharField(max_length=MAX_TEXT_LENGTH)

    class Meta:
        model = Ticket
        fields = ["customer_id", "channel", "text"]


class AgentRunResultSerializer(serializers.ModelSerializer):
    """The parts of an agent run a client needs to see."""

    class Meta:
        model = AgentRun
        fields = ["outcome", "category", "handoff_reason", "answer", "cited_articles", "created_at"]


class TicketSerializer(serializers.ModelSerializer):
    """A ticket as returned by the API, with the latest agent result."""

    result = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ["id", "customer_id", "channel", "text", "status", "created_at", "updated_at", "result"]
        read_only_fields = fields

    def get_result(self, ticket: Ticket) -> dict | None:
        latest_run = next(iter(ticket.runs.all()), None)
        return AgentRunResultSerializer(latest_run).data if latest_run else None