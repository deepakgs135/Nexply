"""Checks the actual retrieval filters, overrides, thresholds, and result shape."""

from unittest.mock import Mock

import pytest

from nexus.services import candidate_memory_retriever as retriever

APP_ID = "0e0b3552-a55d-49e9-97c2-bcc4a311a4c3"


def configured_search(monkeypatch, classification, points=None):
    client = Mock()
    classifier = Mock(return_value=classification)
    client.query_points.return_value.points = points or []
    monkeypatch.setattr(retriever, "generate_embedding", lambda _query: [0.1] * 768)
    monkeypatch.setattr(retriever, "QdrantClient", lambda **_kwargs: client)
    monkeypatch.setattr(retriever, "classify_candidate_query_with_llm", classifier)
    return client, classifier


def test_filter_always_scopes_owner_and_memory_node_and_preserves_results(monkeypatch):
    point = Mock(id="memory-1", score=0.87, payload={"text": "private", "source_section": "skills"})
    client, classifier = configured_search(monkeypatch, {"source_section": "skills"}, [point])
    rows = retriever.search_candidate_memories("skills", APP_ID)
    conditions = client.query_points.call_args.kwargs["query_filter"].must
    assert {item.key: item.match.value for item in conditions} == {
        "app_id": APP_ID, "node_type": "memory", "source_section": "skills"}
    assert rows == [{"memory_id": "memory-1", "score": 0.87, "text": "private",
                     "source_section": "skills", "memory_type": None, "source_index": None, "parent_id": None}]
    classifier.assert_called_once_with("skills")


def test_explicit_section_overrides_classifier_and_score_threshold_is_forwarded(monkeypatch):
    classifier = Mock()
    client, _ = configured_search(monkeypatch, {}, [])
    monkeypatch.setattr(retriever, "classify_candidate_query_with_llm", classifier)
    retriever.search_candidate_memories("anything", APP_ID, score_threshold=0.42, source_section="PROJECTS")
    kwargs = client.query_points.call_args.kwargs
    assert kwargs["score_threshold"] == 0.42
    assert [condition.key for condition in kwargs["query_filter"].must] == ["app_id", "node_type", "source_section"]
    classifier.assert_not_called()


def test_general_search_has_no_section_filter(monkeypatch):
    client, classifier = configured_search(monkeypatch, {"source_section": None}, [])
    assert retriever.search_candidate_memories("overall background", APP_ID) == []
    conditions = client.query_points.call_args.kwargs["query_filter"].must
    assert {item.key for item in conditions} == {"app_id", "node_type"}
    classifier.assert_called_once()


def test_invalid_classifier_section_is_rejected_before_querying_qdrant(monkeypatch):
    client, _ = configured_search(monkeypatch, {"source_section": "untrusted-filter"})
    with pytest.raises(ValueError):
        retriever.search_candidate_memories("some query", APP_ID)
    client.query_points.assert_not_called()


@pytest.mark.parametrize("kwargs", [
    {"source_section": "not-a-section"}, {"score_threshold": 1.1}, {"limit": 0},
    {"app_id": "not-a-uuid"}, {"query": "  "},
])
def test_invalid_inputs_fail_before_qdrant(monkeypatch, kwargs):
    client, _ = configured_search(monkeypatch, {"source_section": None})
    arguments = {"query": "test query", "app_id": APP_ID}
    arguments.update(kwargs)
    with pytest.raises(ValueError):
        retriever.search_candidate_memories(**arguments)
    client.query_points.assert_not_called()
