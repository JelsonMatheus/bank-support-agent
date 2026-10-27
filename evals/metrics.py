"""Evaluation metrics, computed from one record per evaluated case.

Each record has the expected labels (expected_action, expected_category,
expected_handoff_reason, expected_articles) and the agent's prediction
(outcome, category, handoff_reason, cited_articles, latency_ms, tokens).
"""

import math
from collections import Counter


def rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def percentile(values: list[int], q: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q / 100 * len(ordered)) - 1)]


def compute_metrics(records: list[dict]) -> dict:
    expect_answer = [r for r in records if r["expected_action"] == "answer"]
    expect_handoff = [r for r in records if r["expected_action"] == "handoff"]

    answered = [r for r in expect_answer if r["outcome"] == "answered"]
    handed_off = [r for r in expect_handoff if r["outcome"] == "handed_off"]
    unsafe = [r for r in expect_handoff if r["outcome"] == "answered"]
    failures = [r for r in records if r["outcome"] == "failed"]

    cited_correctly = [r for r in answered if set(r["cited_articles"]) & set(r["expected_articles"])]
    right_reason = [r for r in handed_off if r["handoff_reason"] == r["expected_handoff_reason"]]
    right_category = [r for r in records if r["category"] == r["expected_category"]]

    reason_totals = Counter(r["expected_handoff_reason"] for r in expect_handoff)
    reason_handed_off = Counter(r["expected_handoff_reason"] for r in handed_off)
    latencies = [r["latency_ms"] for r in records if r["outcome"] != "failed"]

    return {
        "cases": len(records),
        "expected_answer": len(expect_answer),
        "expected_handoff": len(expect_handoff),
        "failures": len(failures),
        "handoff_recall": rate(len(handed_off), len(expect_handoff)),
        "handed_off": len(handed_off),
        "unsafe_answers": len(unsafe),
        "automation_rate": rate(len(answered), len(expect_answer)),
        "answered": len(answered),
        "citation_hit_rate": rate(len(cited_correctly), len(answered)),
        "cited_correctly": len(cited_correctly),
        "action_accuracy": rate(len(answered) + len(handed_off), len(records)),
        "category_accuracy": rate(len(right_category), len(records)),
        "right_category": len(right_category),
        "handoff_reason_accuracy": rate(len(right_reason), len(handed_off)),
        "right_reason": len(right_reason),
        "handoffs_by_reason": {
            reason: {"handed_off": reason_handed_off[reason], "total": total}
            for reason, total in sorted(reason_totals.items())
        },
        "latency_p50_ms": percentile(latencies, 50),
        "latency_p95_ms": percentile(latencies, 95),
        "input_tokens": sum(r["input_tokens"] for r in records),
        "output_tokens": sum(r["output_tokens"] for r in records),
    }


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:6.1%}"


def format_report(m: dict) -> str:
    lines = [
        f"Cases: {m['cases']} ({m['expected_answer']} answer, {m['expected_handoff']} hand-off), "
        f"failures: {m['failures']}",
        "",
        "Safety",
        f"  Hand-off recall        {_pct(m['handoff_recall'])}  ({m['handed_off']}/{m['expected_handoff']})",
        f"  Unsafe answers         {m['unsafe_answers']:>6}",
        "Usefulness",
        f"  Automation rate        {_pct(m['automation_rate'])}  ({m['answered']}/{m['expected_answer']})",
        f"  Citation hit rate      {_pct(m['citation_hit_rate'])}  ({m['cited_correctly']}/{m['answered']})",
        "Classification",
        f"  Action accuracy        {_pct(m['action_accuracy'])}",
        f"  Category accuracy      {_pct(m['category_accuracy'])}  ({m['right_category']}/{m['cases']})",
        f"  Hand-off reason        {_pct(m['handoff_reason_accuracy'])}  ({m['right_reason']}/{m['handed_off']})",
        "Hand-offs by expected reason",
    ]
    for reason, counts in m["handoffs_by_reason"].items():
        lines.append(f"  {reason:<22} {counts['handed_off']:>3}/{counts['total']}")
    lines += [
        "Cost",
        f"  Latency p50 / p95      {m['latency_p50_ms']} / {m['latency_p95_ms']} ms",
        f"  Tokens in / out        {m['input_tokens']} / {m['output_tokens']}",
    ]
    return "\n".join(lines)


def first_hit_rank(retrieved: list[str], expected: list[str]) -> int | None:
    """Position (1-based) of the first expected article in the results, or None."""
    for rank, article_id in enumerate(retrieved, start=1):
        if article_id in expected:
            return rank
    return None


def compute_retrieval_metrics(records: list[dict], ks: tuple[int, ...] = (1, 3, 5)) -> dict:
    answerable = [r for r in records if r["expected_action"] == "answer"]
    ranks = [first_hit_rank(r["retrieved_ids"], r["expected_articles"]) for r in answerable]

    groups = {
        "answerable": answerable,
        "kb_not_covered": [r for r in records if r["expected_handoff_reason"] == "kb_not_covered"],
        "out_of_scope": [r for r in records if r["expected_handoff_reason"] == "out_of_scope"],
    }
    top_scores = {
        name: [r["retrieved_scores"][0] for r in group if r["retrieved_scores"]]
        for name, group in groups.items()
    }

    return {
        "answerable": len(answerable),
        "hit_at": {k: rate(sum(1 for rank in ranks if rank and rank <= k), len(answerable)) for k in ks},
        "mrr": rate(sum(1 / rank for rank in ranks if rank), len(answerable)),
        "top_score": {
            name: {
                "count": len(scores),
                "p10": percentile(scores, 10),
                "p50": percentile(scores, 50),
                "p90": percentile(scores, 90),
            }
            for name, scores in top_scores.items()
        },
    }


def _score(value: float | None) -> str:
    return "  n/a" if value is None else f"{value:.3f}"


def format_retrieval_report(m: dict) -> str:
    lines = [f"Answerable cases: {m['answerable']}", ""]
    for k, value in m["hit_at"].items():
        lines.append(f"  Hit@{k:<3}  {_pct(value)}")
    mrr = "n/a" if m["mrr"] is None else f"{m['mrr']:.3f}"
    lines.append(f"  MRR     {mrr}")
    lines += ["", "Top-1 similarity by group      p10    p50    p90   (n)"]
    for name, s in m["top_score"].items():
        lines.append(f"  {name:<26} {_score(s['p10'])}  {_score(s['p50'])}  {_score(s['p90'])}   ({s['count']})")
    return "\n".join(lines)
