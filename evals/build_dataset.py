"""Build the development and test sets from BANKING77 and hand-written cases.

Usage:
    uv run python evals/build_dataset.py
"""

import json
import random
from pathlib import Path

from evals.explore_banking77 import load_split

EVALS_DIR = Path(__file__).parent
INTENT_MAP_PATH = EVALS_DIR / "intent_map.json"
HANDWRITTEN_PATH = EVALS_DIR / "data" / "handwritten.jsonl"
OUTPUT_DIR = EVALS_DIR / "datasets"

SPLITS = ("dev", "test")
SOURCE_SPLIT = {"dev": "train", "test": "test"}
SAMPLES_PER_INTENT = {"dev": 6, "test": 10}
SEED = 42


def normalise(text: str) -> str:
    return " ".join(text.lower().split())


def load_intent_map() -> dict:
    return json.loads(INTENT_MAP_PATH.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def labels_for(intent: str, intent_map: dict) -> dict:
    labels = intent_map["intents"][intent]
    return {
        "expected_category": labels["category"],
        "expected_action": labels["action"],
        "expected_handoff_reason": labels["handoff_reason"],
        "expected_articles": labels["articles"],
    }


def sample_banking77(split: str, intent_map: dict, exclude: set[str]) -> list[dict]:
    texts_by_intent: dict[str, set[str]] = {intent: set() for intent in intent_map["intents"]}
    for text, intent in load_split(SOURCE_SPLIT[split]):
        if intent in texts_by_intent and normalise(text) not in exclude:
            texts_by_intent[intent].add(text)

    rng = random.Random(f"{SEED}-{split}")
    cases = []
    for intent in sorted(texts_by_intent):
        candidates = sorted(texts_by_intent[intent])
        for text in rng.sample(candidates, SAMPLES_PER_INTENT[split]):
            cases.append({"text": text, "source": "banking77", "intent": intent, **labels_for(intent, intent_map)})
    return cases


def handwritten_cases(split: str) -> list[dict]:
    cases = []
    for case in load_jsonl(HANDWRITTEN_PATH):
        if case["split"] == split:
            labels = {key: value for key, value in case.items() if key != "split"}
            cases.append({"source": "handwritten", "intent": None, **labels})
    return cases


def build() -> dict[str, list[dict]]:
    intent_map = load_intent_map()
    datasets = {}
    seen: set[str] = set()
    for split in SPLITS:
        cases = sample_banking77(split, intent_map, exclude=seen) + handwritten_cases(split)
        seen |= {normalise(case["text"]) for case in cases}
        datasets[split] = [{"id": f"{split}-{i:04d}", **case} for i, case in enumerate(cases, start=1)]
    return datasets


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    for split, cases in build().items():
        path = OUTPUT_DIR / f"{split}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for case in cases:
                f.write(json.dumps(case, ensure_ascii=False) + "\n")
        handoffs = sum(case["expected_action"] == "handoff" for case in cases)
        print(f"{path}: {len(cases)} cases ({len(cases) - handoffs} answer, {handoffs} handoff)")


if __name__ == "__main__":
    main()