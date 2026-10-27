from django.db import models


class Category(models.TextChoices):
    CARDS = "cards", "Cards"
    PAYMENTS = "payments", "Payments"
    TOP_UP = "top_up", "Top-up"
    TRANSFERS = "transfers", "Transfers"
    ACCOUNT = "account", "Account"
    SECURITY = "security", "Security"
    OTHER = "other", "Other"


class HandoffReason(models.TextChoices):
    # Always hand off (DECISIONS.md, section 4).
    REFUND_OR_DISPUTE = "refund_or_dispute", "Refund or dispute"
    FRAUD_OR_SECURITY = "fraud_or_security", "Fraud or security"
    ACCOUNT_CLOSURE = "account_closure", "Account closure"
    HUMAN_REQUESTED = "human_requested", "Human requested"
    OUT_OF_SCOPE = "out_of_scope", "Out of scope"
    KB_NOT_COVERED = "kb_not_covered", "Not covered by the knowledge base"

    LOW_CONFIDENCE = "low_confidence", "Low classification confidence"
    WEAK_RETRIEVAL = "weak_retrieval", "Weak retrieval"
    TOOL_ERROR = "tool_error", "Tool error"
    AGENT_LIMIT = "agent_limit", "Iteration or time limit"
    INJECTION_SUSPECTED = "injection_suspected", "Suspected prompt injection"
    VALIDATION_FAILED = "validation_failed", "Answer failed validation"
