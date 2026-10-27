from evals.metrics import compute_metrics, percentile


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
    