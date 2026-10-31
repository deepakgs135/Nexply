"""Tests the evaluator with fully mocked classifier and retrieval services."""

from tests.retrieval_evaluation.evaluation_runner import evaluate_queries

QUERY = {"query_id": "skills-01", "query": "List all skills.", "category": "technical_skills",
         "expected_intent": "SKILL_SEARCH", "expected_source_sections": ["skills"],
         "relevant_memory_ids": ["a", "b"], "relevance_note": "Requests every skill."}


def test_runner_computes_threshold_k_classification_and_category_metrics():
    calls = []
    def classifier(query):
        return {"intent": "SKILL_SEARCH", "source_section": "skills", "classifier": "llm"}
    def retriever(query, app_id, limit, classification):
        calls.append((app_id, limit, classification["source_section"]))
        return [{"memory_id": "a", "score": 0.9, "source_section": "skills"},
                {"memory_id": "not-relevant", "score": 0.3, "source_section": "skills"}]
    report = evaluate_queries([QUERY], "test-owner", classifier, retriever,
                              k_values=[1, 3], thresholds=[None, 0.4])
    assert report["query_count"] == 1
    assert report["runs_by_threshold"]["None"]["overall"]["intent_accuracy"] == 1.0
    assert report["runs_by_threshold"]["0.4"]["by_category"]["technical_skills"]["metrics_at_k"]["3"]["recall"] == 0.5
    assert report["runs_by_threshold"]["0.4"]["queries"][0]["result_count"] == 1
    assert len(calls) == 1 and calls[0][1] == 3


def test_runner_records_service_errors_as_empty_failed_queries():
    def fail(*_args):
        raise RuntimeError("service unavailable")
    report = evaluate_queries([QUERY], "test-owner", fail, fail, k_values=[1])
    row = report["runs_by_threshold"]["None"]["queries"][0]
    assert row["error_type"] == "RuntimeError"
    assert row["result_count"] == 0
    assert report["runs_by_threshold"]["None"]["overall"]["error_rate"] == 1.0
