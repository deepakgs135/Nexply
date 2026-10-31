"""Candidate-scope checks reject missing and cross-candidate relevance labels."""

from unittest.mock import Mock

import pytest

from tests.retrieval_evaluation import scope_validation

APP_ID = "0e0b3552-a55d-49e9-97c2-bcc4a311a4c3"


def test_label_validator_requires_owner_and_memory_type(monkeypatch):
    client = Mock()
    client.retrieve.return_value = [Mock(id="memory", payload={"app_id": APP_ID, "node_type": "memory"})]
    monkeypatch.setattr(scope_validation, "QdrantClient", lambda **_kwargs: client)
    scope_validation.validate_label_ownership(APP_ID, ["memory"])
    client.retrieve.assert_called_once()


@pytest.mark.parametrize("payload", [
    {"app_id": "another-owner", "node_type": "memory"},
    {"app_id": APP_ID, "node_type": "section"},
])
def test_label_validator_rejects_foreign_or_nonmemory_points(monkeypatch, payload):
    client = Mock()
    client.retrieve.return_value = [Mock(id="memory", payload=payload)]
    monkeypatch.setattr(scope_validation, "QdrantClient", lambda **_kwargs: client)
    with pytest.raises(ValueError):
        scope_validation.validate_label_ownership(APP_ID, ["memory"])
