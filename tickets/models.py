import uuid

from django.db import models
from django.db.models import Q

from tickets.choices import Category, HandoffReason


# Create your models here.

class Ticket(models.Model):
    """A message sent by a customer, and where its handling stands."""

    class Channel(models.TextChoices):
        CHAT = "chat", "Chat"
        EMAIL = "email", "Email"

    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PROCESSING = "processing", "Processing"
        ANSWERED = "answered", "Answered"
        HANDED_OFF = "handed_off", "Handed off"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.CharField(max_length=64)
    channel = models.CharField(max_length=16, choices=Channel.choices, default=Channel.CHAT)
    text = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RECEIVED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self) -> str:
        return f"{self.id} ({self.status})"


class AgentRun(models.Model):
    """One execution of the agent on a ticket: its decision, cost and trace."""

    class Outcome(models.TextChoices):
        ANSWERED = "answered", "Answered"
        HANDED_OFF = "handed_off", "Handed off"
        FAILED = "failed", "Failed"

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="runs")
    outcome = models.CharField(max_length=16, choices=Outcome.choices)

    category = models.CharField(max_length=16, choices=Category.choices, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    handoff_reason = models.CharField(max_length=32, choices=HandoffReason.choices, blank=True)
    answer = models.TextField(blank=True)
    cited_articles = models.JSONField(default=list, blank=True)
    error = models.TextField(blank=True)

    model_name = models.CharField(max_length=64, blank=True)
    prompt_version = models.CharField(max_length=32, blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    latency_ms = models.PositiveIntegerField(default=0)
    trace_id = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                name="agent_run_answer_has_text_and_no_reason",
                condition=~Q(outcome="answered") | (Q(handoff_reason="") & ~Q(answer="")),
            ),
            models.CheckConstraint(
                name="agent_run_handoff_has_reason",
                condition=~Q(outcome="handed_off") | ~Q(handoff_reason=""),
            ),
            models.CheckConstraint(
                name="agent_run_failure_has_error",
                condition=~Q(outcome="failed") | ~Q(error=""),
            ),
            models.CheckConstraint(
                name="agent_run_confidence_between_0_and_1",
                condition=Q(confidence__isnull=True) | Q(confidence__gte=0, confidence__lte=1),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.ticket_id}: {self.outcome}"