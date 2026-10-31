"""Tests LLM-primary intent classification and its safe regex fallback."""

import json
from unittest.mock import Mock

import pytest
import requests

from nexus.services import candidate_llm_intent_classifier as classifier
from nexus.services.candidate_query_classifier import classify_candidate_query


def test_valid_ollama_classification_is_primary(monkeypatch):
    response = Mock()
    response.json.return_value = {"message": {"content": json.dumps({"intent": "PROJECT_SEARCH",
        "source_section": "projects", "confidence": 0.9, "reason": "Project request."})}}
    monkeypatch.setattr(classifier.requests, "post", Mock(return_value=response))
    result = classifier.classify_candidate_query_with_llm("What projects are listed?")
    assert result["classifier"] == "llm" and result["source_section"] == "projects"


def test_connection_failure_falls_back_to_regex(monkeypatch):
    monkeypatch.setattr(classifier.requests, "post", Mock(side_effect=requests.ConnectionError()))
    result = classifier.classify_candidate_query_with_llm("Which skills are listed?")
    assert result["classifier"] == "regex_fallback" and result["intent"] == "SKILL_SEARCH"


@pytest.mark.parametrize("payload", [
    {"intent": "NOT_ALLOWED", "source_section": "invalid", "confidence": 1, "reason": "bad"},
    {"intent": "PROJECT_SEARCH", "source_section": "skills", "confidence": 1, "reason": "bad map"},
    {"intent": "SKILL_SEARCH", "source_section": "skills", "confidence": 2, "reason": "bad score"},
])
def test_invalid_llm_payload_uses_regex_fallback(monkeypatch, payload):
    response = Mock()
    response.json.return_value = {"message": {"content": json.dumps(payload)}}
    monkeypatch.setattr(classifier.requests, "post", Mock(return_value=response))
    result = classifier.classify_candidate_query_with_llm("Which skills are listed?")
    assert result["classifier"] == "regex_fallback"
    assert result["source_section"] == "skills"


def test_regex_marks_multi_category_query_general_and_empty_query_rejected(monkeypatch):
    assert classify_candidate_query("List skills and projects") ["intent"] == "GENERAL_SEARCH"
    post = Mock()
    monkeypatch.setattr(classifier.requests, "post", post)
    with pytest.raises(ValueError):
        classifier.classify_candidate_query_with_llm("   ")
    post.assert_not_called()
