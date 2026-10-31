"""Pure, dependency-free ranking and classification metrics."""

from collections.abc import Iterable
from typing import Any


def _ids(items: Iterable[Any]) -> list[str]:
    """Extract unique memory IDs in rank order, retaining the first occurrence."""
    result, seen = [], set()
    for item in items:
        value = item.get("memory_id") if isinstance(item, dict) else item
        if value is not None and str(value) not in seen:
            seen.add(str(value))
            result.append(str(value))
    return result


def precision_at_k(retrieved: Iterable[Any], relevant: Iterable[Any], k: int) -> float:
    """Return relevant unique results divided by unique results actually returned up to K."""
    ranked = _ids(retrieved)[:_positive_k(k)]
    relevant_ids = set(_ids(relevant))
    return sum(item in relevant_ids for item in ranked) / len(ranked) if ranked else 0.0


def recall_at_k(retrieved: Iterable[Any], relevant: Iterable[Any], k: int) -> float:
    """Return the fraction of unique known relevant IDs retrieved by K."""
    relevant_ids = set(_ids(relevant))
    if not relevant_ids:
        return 0.0
    return len(set(_ids(retrieved)[:_positive_k(k)]) & relevant_ids) / len(relevant_ids)


def reciprocal_rank(retrieved: Iterable[Any], relevant: Iterable[Any]) -> float:
    """Return the reciprocal rank of the first relevant result, or zero."""
    relevant_ids = set(_ids(relevant))
    return next((1.0 / rank for rank, item in enumerate(_ids(retrieved), 1) if item in relevant_ids), 0.0)


def hit_rate_at_k(retrieved: Iterable[Any], relevant: Iterable[Any], k: int) -> float:
    """Return one when any relevant unique memory appears in the first K results."""
    relevant_ids = set(_ids(relevant))
    return float(bool(set(_ids(retrieved)[:_positive_k(k)]) & relevant_ids))


def _positive_k(k: int) -> int:
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError("K must be a positive integer.")
    return k
