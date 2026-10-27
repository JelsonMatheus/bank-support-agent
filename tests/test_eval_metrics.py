import pytest

from evals.metrics import compute_metrics, percentile
from evals.metrics import compute_retrieval_metrics, first_hit_rank
from agent.baseline import BaselineAgent
from evals.run_eval import evaluate


class FailingAgent:
    def run(self, text, customer_id):
        raise RuntimeError("provider timeout")


CASES = [
    {"id": f"dev-000{i}", "text": f"message {i}", "intent": "card_arrival", "expected_category": "cards",
     "expected_action": "answer", "expected_handoff_reason": None, "expected_articles": ["kb-002"]}
    for i in range(1, 4)
]


def record(expected_action, outcome, **overrides) -> dict:
    base = {
        "expected_action": expected_action,
        "expected_category": "cards",
        "expected_handoff_reason": "refund_or_dispute" if expected_action == "handoff" else None,
        "expected_articles": ["kb-002"] if expected_action == "answer" else [],
        "outcome": outcome,
        "category": "cards",
        "handoff_reason": "",
        "cited_articles": [],
        "latency_ms": 100,
        "input_tokens": 10,
        "output_tokens": 5,
    }
    return {**base, **overrides}


def test_answering_a_hand_off_case_is_unsafe():
    metrics = compute_metrics([
        record("handoff", "handed_off", handoff_reason="refund_or_dispute"),
        record("handoff", "answered"),
    ])

    assert metrics["unsafe_answers"] == 1
    assert metrics["handoff_recall"] == 0.5
    assert metrics["handoff_reason_accuracy"] == 1.0


def test_automation_and_citations_only_count_correct_answers():
    metrics = compute_metrics([
        record("answer", "answered", cited_articles=["kb-002"]),
        record("answer", "answered", cited_articles=["kb-009"]),
        record("answer", "handed_off", handoff_reason="low_confidence"),
    ])

    assert metrics["automation_rate"] == 2 / 3
    assert metrics["citation_hit_rate"] == 0.5


def test_failures_count_as_neither_safe_nor_useful():
    metrics = compute_metrics([record("handoff", "failed"), record("answer", "failed")])

    assert metrics["failures"] == 2
    assert metrics["handoff_recall"] == 0.0
    assert metrics["automation_rate"] == 0.0
    assert metrics["latency_p50_ms"] is None


def test_rates_without_cases_are_not_reported_as_zero():
    metrics = compute_metrics([record("handoff", "handed_off", handoff_reason="refund_or_dispute")])

    assert metrics["automation_rate"] is None
    assert metrics["citation_hit_rate"] is None


def test_hand_offs_are_broken_down_by_expected_reason():
    metrics = compute_metrics([
        record("handoff", "handed_off", expected_handoff_reason="fraud_or_security"),
        record("handoff", "answered", expected_handoff_reason="fraud_or_security"),
        record("handoff", "handed_off", expected_handoff_reason="kb_not_covered"),
    ])

    assert metrics["handoffs_by_reason"] == {
        "fraud_or_security": {"handed_off": 1, "total": 2},
        "kb_not_covered": {"handed_off": 1, "total": 1},
    }


def test_percentile_uses_nearest_rank():
    assert percentile([10, 20, 30, 40], 50) == 20
    assert percentile([10, 20, 30, 40], 95) == 40


def test_evaluate_keeps_case_order_and_labels():
    records = evaluate(CASES, BaselineAgent(), workers=2)

    assert [r["id"] for r in records] == ["dev-0001", "dev-0002", "dev-0003"]
    assert all(r["outcome"] == "handed_off" and r["expected_action"] == "answer" for r in records)


def test_evaluate_records_agent_errors_instead_of_stopping():
    records = evaluate(CASES, FailingAgent(), workers=2)

    assert all(r["outcome"] == "failed" for r in records)
    assert "provider timeout" in records[0]["error"]


def retrieval_record(expected_action, retrieved_ids, scores, expected_articles=(), reason=None) -> dict:
    return {
        "expected_action": expected_action,
        "expected_articles": list(expected_articles),
        "expected_handoff_reason": reason,
        "retrieved_ids": retrieved_ids,
        "retrieved_scores": scores,
    }


def test_first_hit_rank_accepts_any_expected_article():
    assert first_hit_rank(["kb-009", "kb-005", "kb-003"], ["kb-003", "kb-005"]) == 2
    assert first_hit_rank(["kb-009"], ["kb-003"]) is None


def test_hit_at_k_and_mrr():
    metrics = compute_retrieval_metrics([
        retrieval_record("answer", ["kb-002", "kb-001", "kb-003"], [0.9, 0.8, 0.7], ["kb-002"]),
        retrieval_record("answer", ["kb-001", "kb-003", "kb-002"], [0.9, 0.8, 0.7], ["kb-002"]),
        retrieval_record("answer", ["kb-001", "kb-003", "kb-004"], [0.9, 0.8, 0.7], ["kb-002"]),
    ], ks=(1, 3))

    assert metrics["hit_at"] == {1: 1 / 3, 3: 2 / 3}
    assert metrics["mrr"] == pytest.approx((1 + 1 / 3 + 0) / 3)


def test_top_scores_are_grouped_by_expected_behaviour():
    metrics = compute_retrieval_metrics([
        retrieval_record("answer", ["kb-002"], [0.85], ["kb-002"]),
        retrieval_record("handoff", ["kb-010"], [0.55], reason="kb_not_covered"),
        retrieval_record("handoff", ["kb-017"], [0.40], reason="out_of_scope"),
        retrieval_record("handoff", ["kb-006"], [0.80], reason="refund_or_dispute"),
    ])

    assert metrics["top_score"]["answerable"]["p50"] == 0.85
    assert metrics["top_score"]["kb_not_covered"]["p50"] == 0.55
    assert metrics["top_score"]["out_of_scope"]["p50"] == 0.40
