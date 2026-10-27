from agent.types import AgentResult


class BaselineAgent:
    """Hands every message off to a human.

    The safest possible agent, and the reference point for evaluation: it never
    answers wrongly, and never answers at all. A real agent has to answer more
    without losing that safety.
    """

    def run(self, text: str, customer_id: str) -> AgentResult:
        return AgentResult(
            outcome="handed_off",
            handoff_reason="low_confidence",
            confidence=0.0,
            prompt_version="baseline",
        )