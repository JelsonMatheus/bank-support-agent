"""Explore the BANKING77 dataset: intent counts, text lengths and samples.

Usage:
    uv run python evals/explore_banking77.py
    uv run python evals/explore_banking77.py --intent card_arrival
    uv run python evals/explore_banking77.py --check card_arrival request_refund
"""

import argparse
import csv
import random
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data" / "banking77"
SPLITS = ("train", "test")


def load_split(split: str) -> list[tuple[str, str]]:
    """Return (text, intent) pairs from one split, skipping the header row."""
    with open(DATA_DIR / f"{split}.csv", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        return [(text, intent) for text, intent in reader]


def show_summary() -> None:
    for split in SPLITS:
        rows = load_split(split)
        intents = Counter(intent for _, intent in rows)
        average_length = sum(len(text) for text, _ in rows) / len(rows)
        print(
            f"{split}: {len(rows)} messages, {len(intents)} intents, "
            f"average length {average_length:.0f} characters"
        )

    print("\nMessages per intent (train):")
    counts = Counter(intent for _, intent in load_split("train"))
    for intent, count in counts.most_common():
        print(f"{count:5d}  {intent}")


def show_samples(intent: str, n: int, seed: int) -> None:
    texts = [text for text, label in load_split("train") if label == intent]
    if not texts:
        raise SystemExit(f"Unknown intent: {intent}")
    random.Random(seed).shuffle(texts)
    print(f"{intent} ({len(texts)} messages in train), {min(n, len(texts))} samples:")
    for text in texts[:n]:
        print(f"- {text}")


def check_intents(intents: list[str]) -> None:
    known = {intent for _, intent in load_split("train")}
    missing = [intent for intent in intents if intent not in known]
    if missing:
        print(f"Missing: {', '.join(missing)}")
    else:
        print(f"All {len(intents)} intents found.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--intent", help="show sample messages for this intent")
    parser.add_argument("--n", type=int, default=10, help="number of samples")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument("--check", nargs="+", metavar="INTENT", help="check that intents exist")
    args = parser.parse_args()

    if args.check:
        check_intents(args.check)
    elif args.intent:
        show_samples(args.intent, args.n, args.seed)
    else:
        show_summary()


if __name__ == "__main__":
    main()
