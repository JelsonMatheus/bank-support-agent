"""Run an agent on an evaluation set and report the metrics.

Usage (from the project root):
    uv run python -m evals.run_eval --agent baseline
    uv run python -m evals.run_eval --agent baseline --limit 20
    uv run python -m evals.run_eval --agent baseline --split test --allow-test
"""

import argparse
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from agent.types import Agent, AgentResult
from evals.build_dataset import OUTPUT_DIR as DATASETS_DIR
from evals.build_dataset import load_jsonl
from evals.metrics import compute_metrics, format_report

RESULTS_DIR = Path(__file__).parent / "results"
EVAL_CUSTOMER_ID = "c-0001"
EXPECTED_FIELDS = ("id", "text", "intent", "expected_category", "expected_action",
                   "expected_handoff_reason", "expected_articles")


def run_case(agent: Agent, case: dict) -> dict:
    started = time.perf_counter()
    try:
        prediction = asdict(agent.run(case["text"], customer_id=EVAL_CUSTOMER_ID))
        error = ""
    except Exception as exc:
        prediction = asdict(AgentResult(outcome="failed"))
        error = repr(exc)
    latency_ms = int((time.perf_counter() - started) * 1000)
    return {**{key: case[key] for key in EXPECTED_FIELDS}, **prediction, "error": error, "latency_ms": latency_ms}


def evaluate(cases: list[dict], agent: Agent, workers: int = 1) -> list[dict]:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda case: run_case(agent, case), cases))


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def save_results(records: list[dict], metrics: dict, config: dict) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    run_dir = RESULTS_DIR / f"{stamp}-{config['split']}-{config['agent']}"
    run_dir.mkdir(parents=True)
    with open(run_dir / "cases.jsonl", "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    (run_dir / "summary.json").write_text(json.dumps({"config": config, "metrics": metrics}, indent=2), encoding="utf-8")
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an agent on an evaluation set.")
    parser.add_argument("--agent", default="baseline", help="agent name from agent/registry.py")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--allow-test", action="store_true", help="required to run on the test set")
    parser.add_argument("--limit", type=int, help="evaluate only the first N cases")
    parser.add_argument("--workers", type=int, default=4, help="cases evaluated in parallel")
    args = parser.parse_args()

    if args.split == "test" and not args.allow_test:
        parser.error("the test set is run once, at the end; pass --allow-test to confirm")

    # The LLM agent will query the knowledge base through Django.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from agent.registry import get_agent

    cases = load_jsonl(DATASETS_DIR / f"{args.split}.jsonl")[: args.limit]
    records = evaluate(cases, get_agent(args.agent), workers=args.workers)
    metrics = compute_metrics(records)

    config = {"agent": args.agent, "split": args.split, "limit": args.limit, "commit": git_commit()}
    run_dir = save_results(records, metrics, config)

    print(format_report(metrics))
    print(f"\nSaved to {run_dir}")


if __name__ == "__main__":
    main()
