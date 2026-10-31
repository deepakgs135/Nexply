"""Opt-in local smoke test for Ollama embedding/classification and Qdrant search."""

import os
import uuid

import pytest

from nexus.services.candidate_memory_retriever import search_candidate_memories
from nexus.services.embedding_service import generate_embedding

pytestmark = pytest.mark.skipif(
    os.getenv("NEXPLY_RUN_LIVE_RETRIEVAL") != "1" or not os.getenv("NEXPLY_APP_ID"),
    reason="Set NEXPLY_RUN_LIVE_RETRIEVAL=1 and NEXPLY_APP_ID for local service smoke testing.",
)


def test_live_embedding_and_candidate_scoped_qdrant_search():
    app_id = str(uuid.UUID(os.environ["NEXPLY_APP_ID"]))
    vector = generate_embedding("candidate profile skills")
    assert len(vector) == 768
    results = search_candidate_memories("List every technical skill recorded for this candidate.", app_id, limit=3)
    assert isinstance(results, list)
    assert len(results) <= 3
    assert all(result["source_section"] == "skills" for result in results)
