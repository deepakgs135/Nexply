"""Run annotated queries through injected classifier and retrieval services."""

from collections.abc import Callable
from time import perf_counter
from typing import Any

from tests.retrieval_evaluation.metrics import hit_rate_at_k, precision_at_k, recall_at_k, reciprocal_rank

Classifier = Callable[[str], dict]
Retriever = Callable[[str, str, int, dict], list[dict]]
Progress = Callable[[int, int], None]


def evaluate_queries(queries: list[dict], app_id: str, classifier: Classifier,
                     retriever: Retriever, k_values=(1, 3, 5, 10),
                     thresholds=(None,), progress: Progress | None = None) -> dict[str, Any]:
    """Evaluate classifier and ranked retrieval at each K and score threshold."""
    if not queries:
        raise ValueError("At least one evaluation query is required.")
    ks = sorted(set(k_values))
    if not ks or any(isinstance(k, bool) or not isinstance(k, int) or k < 1 for k in ks):
        raise ValueError("K values must be positive integers.")
    thresholds = tuple(thresholds)
    if not thresholds or any(t is not None and (not isinstance(t, (int, float)) or not 0 <= t <= 1) for t in thresholds):
        raise ValueError("Thresholds must be null or between zero and one.")
    per_threshold = {str(t): [] for t in thresholds}
    for query_index, query in enumerate(queries, 1):
        started = perf_counter()
        try:
            classification = classifier(query["query"])
            classification_ms = (perf_counter() - started) * 1000
        except Exception as exc:
            for threshold in thresholds:
                per_threshold[str(threshold)].append(_error_row(
                    query, ks, type(exc).__name__, (perf_counter() - started) * 1000))
            if progress:
                progress(query_index, len(queries))
            continue
        try:
            retrieval_started = perf_counter()
            raw_results = retriever(query["query"], app_id, max(ks), classification)
            latency_ms = classification_ms + (perf_counter() - retrieval_started) * 1000
        except Exception as exc:
            for threshold in thresholds:
                row = _error_row(query, ks, type(exc).__name__, classification_ms + (perf_counter() - retrieval_started) * 1000)
                per_threshold[str(threshold)].append(row)
            if progress:
                progress(query_index, len(queries))
            continue
        for threshold in thresholds:
            filtered = [item for item in raw_results if threshold is None or item.get("score", 0) >= threshold]
            row = _score_query(query, classification, filtered[:max(ks)], ks, latency_ms)
            per_threshold[str(threshold)].append(row)
        if progress:
            progress(query_index, len(queries))
    from tests.retrieval_evaluation.report_writer import summarize_results
    return summarize_results(queries, per_threshold, ks, thresholds)


def _score_query(query: dict, classification: dict, results: list[dict], ks: list[int], latency_ms: float) -> dict:
    ids = [item.get("memory_id") for item in results if item.get("memory_id") is not None]
    relevant = query["relevant_memory_ids"]
    metrics = {str(k): {"precision": precision_at_k(ids, relevant, k),
                        "recall": recall_at_k(ids, relevant, k),
                        "mrr": reciprocal_rank(ids[:k], relevant),
                        "hit_rate": hit_rate_at_k(ids, relevant, k)} for k in ks}
    return {"query_id": query["query_id"], "category": query["category"],
            "expected_intent": query["expected_intent"], "actual_intent": classification.get("intent"),
            "expected_source_sections": query["expected_source_sections"],
            "actual_source_section": classification.get("source_section"),
            "classifier": classification.get("classifier"), "result_count": len(set(ids)),
            "retrieved": [{"memory_id": item.get("memory_id"), "score": item.get("score"),
                           "source_section": item.get("source_section")} for item in results],
            "latency_ms": round(latency_ms, 3), "metrics_at_k": metrics, "error_type": None}


def _error_row(query: dict, ks: list[int], error_type: str, latency_ms: float = 0.0) -> dict:
    empty = {str(k): {"precision": 0.0, "recall": 0.0, "mrr": 0.0, "hit_rate": 0.0} for k in ks}
    return {"query_id": query["query_id"], "category": query["category"],
            "expected_intent": query["expected_intent"], "actual_intent": None,
            "expected_source_sections": query["expected_source_sections"], "actual_source_section": None,
            "classifier": None, "result_count": 0, "retrieved": [], "latency_ms": round(latency_ms, 3),
            "metrics_at_k": empty, "error_type": error_type}


