"""Checks query coverage and the candidate-specific annotation format."""

import json
from collections import Counter

import pytest

from tests.retrieval_evaluation.dataset import build_dataset, load_dataset
from tests.retrieval_evaluation.query_catalog import QUERY_SPECS


def test_catalog_has_required_category_coverage():
    counts = Counter(query.category for query in QUERY_SPECS)
    assert len(QUERY_SPECS) >= 40
    assert counts["technical_skills"] >= 6
    assert counts["projects"] >= 6
    assert counts["work_experience"] >= 6
    assert counts["education"] >= 4
    assert counts["certifications"] >= 4
    assert counts["general_profile"] >= 5
    assert counts["multi_section"] >= 5
    assert counts["paraphrased_challenging"] >= 4


def test_build_dataset_assigns_only_requested_sections_without_source_text():
    query = QUERY_SPECS[0]
    built = build_dataset([query], {"skills": ["opaque-skill-id"]})["queries"][0]
    assert built["relevant_memory_ids"] == ["opaque-skill-id"]
    assert "text" not in built and "app_id" not in built
    assert built["expected_source_sections"] == ["skills"]


def test_loader_validates_annotation_fields_and_relevance(tmp_path):
    payload = {"queries": [{"query_id": "q", "query": "Which skills?", "category": "technical_skills",
                "expected_intent": "SKILL_SEARCH", "expected_source_sections": ["skills"],
                "relevant_memory_ids": ["id-1"], "relevance_note": "Requests skills."}]}
    path = tmp_path / "queries.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert load_dataset(path, require_phase5_coverage=False)[0]["query_id"] == "q"
    payload["queries"][0]["expected_intent"] = "UNKNOWN"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        load_dataset(path, require_phase5_coverage=False)
