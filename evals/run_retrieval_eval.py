"""Evaluate retrieval alone: does search find the expected article?

Usage (from the project root):
    uv run python -m evals.run_retrieval_eval
    uv run python -m evals.run_retrieval_eval --show-misses
"""

import argparse
import json
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from evals.build_dataset import OUTPUT_DIR as DATASETS_DIR
from evals.build_dataset import load_jsonl
from evals.metrics import compute_retrieval_metrics, first_hit_rank, format_retrieval_report
from evals.run_eval import EXPECTED_FIELDS, RESULTS_DIR, git_commit


def evaluate_retrieval(cases: list[dict], search: Callable, k: int, workers: int = 1) -> list[dict]:
    def run(case: dict) -> dict:
        results = search(case["text"], k=k)
        return {
            **{key: case[key] for key in EXPECTED_FIELDS},
            "retrieved_ids": [r.article_id for r in results],
            "retrieved_scores": [round(r.score, 4) for r in results],
        }

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(run, cases))


def print_misses(records: list[dict]) -> None:
    misses = [
        r for r in records
        if r["expected_action"] == "answer" and first_hit_rank(r["retrieved_ids"], r["expected_articles"]) != 1
    ]
    print(f"\nAnswerable cases where the expected article was not first: {len(misses)}")
    for r in misses:
        found = ", ".join(f"{i} ({s:.2f})" for i, s in zip(r["retrieved_ids"][:3], r["retrieved_scores"][:3]))
        print(f"\n  {r['id']}  [{r['intent']}]  {r['text']}")
        print(f"    expected: {', '.join(r['expected_articles'])}")
        print(f"    found:    {found}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate knowledge base retrieval.")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--allow-test", action="store_true", help="required to run on the test set")
    parser.add_argument("--k", type=int, default=5, help="number of articles to retrieve")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--show-misses", action="store_true", help="list cases where the expected article wasn't first")
    args = parser.parse_args()

    if args.split == "test" and not args.allow_test:
        parser.error("the test set is run once, at the end; pass --allow-test to confirm")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from knowledge.embeddings import model_name
    from knowledge.retrieval import search

    cases = load_jsonl(DATASETS_DIR / f"{args.split}.jsonl")
    records = evaluate_retrieval(cases, search, k=args.k, workers=args.workers)
    ks = tuple(k for k in (1, 3, 5) if k <= args.k)
    metrics = compute_retrieval_metrics(records, ks=ks)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    run_dir = RESULTS_DIR / f"{stamp}-{args.split}-retrieval"
    run_dir.mkdir(parents=True)
    with open(run_dir / "cases.jsonl", "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    config = {"split": args.split, "k": args.k, "embedding_model": model_name(), "commit": git_commit()}
    (run_dir / "summary.json").write_text(json.dumps({"config": config, "metrics": metrics}, indent=2), encoding="utf-8")

    print(format_retrieval_report(metrics))
    if args.show_misses:
        print_misses(records)
    print(f"\nSaved to {run_dir}")


if __name__ == "__main__":
    main()
    