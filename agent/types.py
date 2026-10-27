"""The contract between the agent and the rest of the system."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class AgentResult:
    """The agent's decision on one message.

    `outcome` is "answered" or "handed_off". Failures are raised as exceptions,
    never returned as results.
    """

    outcome: str
    category: str = ""
    confidence: float | None = None
    handoff_reason: str = ""
    answer: str = ""
    cited_articles: list[str] = field(default_factory=list)
    model_name: str = ""
    prompt_version: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    trace_id: str = ""


class Agent(Protocol):
    def run(self, text: str, customer_id: str) -> AgentResult: ...
    