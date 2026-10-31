"""Verify relevance labels belong only to the selected candidate."""

import uuid
from collections.abc import Iterable

from qdrant_client import QdrantClient

COLLECTION = "candidate_memory_v1"
QDRANT_URL = "http://127.0.0.1:6333"


def validate_label_ownership(app_id: str, memory_ids: Iterable[str]) -> None:
    """Fail closed unless every label resolves to this candidate's memory node."""
    candidate_id = str(uuid.UUID(str(app_id)))
    ids = sorted(set(map(str, memory_ids)))
    if not ids:
        raise ValueError("Evaluation dataset has no relevance labels.")
    client = QdrantClient(url=QDRANT_URL, timeout=10)
    points = client.retrieve(COLLECTION, ids=ids, with_payload=["app_id", "node_type"], with_vectors=False)
    valid = {str(point.id) for point in points
             if (point.payload or {}).get("app_id") == candidate_id
             and (point.payload or {}).get("node_type") == "memory"}
    if valid != set(ids):
        raise ValueError("Evaluation relevance labels are missing or outside the selected candidate scope.")
