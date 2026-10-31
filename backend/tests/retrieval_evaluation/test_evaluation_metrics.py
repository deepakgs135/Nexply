"""Edge-case coverage for the standalone ranking metrics."""

import pytest

from tests.retrieval_evaluation.metrics import (
    hit_rate_at_k, precision_at_k, recall_at_k, reciprocal_rank,
)


def test_precision_uses_unique_results_actually_returned_up_to_k():
    ranked = [{"memory_id": "a"}, {"memory_id": "a"}, {"memory_id": "b"}]
    assert precision_at_k(ranked, ["a"], 3) == 0.5


def test_recall_counts_distinct_relevant_ids_and_safe_zero_relevance():
    assert recall_at_k(["a", "a", "b"], ["a", "b", "c"], 3) == pytest.approx(2 / 3)
    assert recall_at_k(["a"], [], 1) == 0.0


def test_reciprocal_rank_uses_first_relevant_unique_result():
    assert reciprocal_rank(["x", "x", "b"], ["b"]) == 0.5
    assert reciprocal_rank(["x"], ["b"]) == 0.0


def test_hit_rate_handles_empty_results_and_cutoff():
    assert hit_rate_at_k(["x", "b"], ["b"], 1) == 0.0
    assert hit_rate_at_k(["x", "b"], ["b"], 2) == 1.0
    assert hit_rate_at_k([], ["b"], 5) == 0.0


@pytest.mark.parametrize("k", [0, -1, True, 1.5])
def test_metrics_reject_invalid_k(k):
    with pytest.raises(ValueError):
        precision_at_k([], [], k)
