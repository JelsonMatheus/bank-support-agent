from agent.baseline import BaselineAgent
from agent.types import Agent

AGENTS = {"baseline": BaselineAgent}


def get_agent(name: str) -> Agent:
    try:
        return AGENTS[name]()
    except KeyError:
        raise ValueError(f"Unknown agent {name!r}. Available: {sorted(AGENTS)}") from None
    