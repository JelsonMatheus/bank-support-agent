import json
from pathlib import Path

import pytest

from evals.explore_banking77 import load_split

INTENT_MAP_PATH = Path(__file__).parent.parent / "evals" / "intent_map.json"


@pytest.fixture(scope="module")
def intent_map() -> dict:
    return json.loads(INTENT_MAP_PATH.read_text(encoding="utf-8"))


def test_every_mapped_intent_exists_in_dataset(intent_map):
    known = {intent for _, intent in load_split("train")}
    unknown = set(intent_map["intents"]) - known
    assert not unknown, f"Intents not in BANKING77: {sorted(unknown)}"


def test_categories_and_reasons_are_allowed(intent_map):
    categories = set(intent_map["categories"])
    reasons = set(intent_map["handoff_reasons"])
    for intent, labels in intent_map["intents"].items():
        assert labels["category"] in categories, intent
        if labels["handoff_reason"] is not None:
            assert labels["handoff_reason"] in reasons, intent


def test_action_and_reason_are_consistent(intent_map):
    for intent, labels in intent_map["intents"].items():
        if labels["action"] == "answer":
            assert labels["handoff_reason"] is None, f"{intent}: answer with a reason"
        elif labels["action"] == "handoff":
            assert labels["handoff_reason"] is not None, f"{intent}: handoff without a reason"
        else:
            pytest.fail(f"{intent}: unknown action {labels['action']!r}")

