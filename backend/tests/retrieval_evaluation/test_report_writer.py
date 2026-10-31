"""Verifies JSON and readable report output without candidate identifiers."""

import json

from tests.retrieval_evaluation.report_writer import write_reports


def test_report_writer_creates_both_formats_and_preserves_privacy(tmp_path):
    report = {"query_count": 1, "k_values": [1], "thresholds": [None], "runs_by_threshold": {
        "None": {"overall": {"intent_accuracy": 1.0, "section_accuracy": 1.0,
        "empty_result_rate": 0.0, "metrics_at_k": {"1": {"precision": 1.0, "recall": 0.5,
        "mrr": 1.0, "hit_rate": 1.0}}}, "by_category": {"skills": {"query_count": 1,
        "metrics_at_k": {"1": {"precision": 1.0, "recall": 0.5, "mrr": 1.0,
        "hit_rate": 1.0}}, "empty_result_rate": 0.0, "average_latency_ms": 2}}, "queries": []}}}
    json_path, md_path = write_reports(report, tmp_path, "unit")
    assert json.loads(json_path.read_text())["run_name"] == "unit"
    assert "app_id" not in json_path.read_text()
    assert "skills" in md_path.read_text()
