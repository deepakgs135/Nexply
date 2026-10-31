"""Bind the reviewable query catalog to one candidate's indexed memory IDs."""

import json
import os
import uuid
from collections import defaultdict
from pathlib import Path

from qdrant_client import QdrantClient, models

from tests.retrieval_evaluation.dataset import build_dataset
from tests.retrieval_evaluation.query_catalog import QUERY_SPECS

COLLECTION = "candidate_memory_v1"
OUTPUT = Path(__file__).with_name("test_queries.json")


def read_memory_ids(app_id: str) -> dict[str, list[str]]:
    """Read only IDs and section labels for this candidate, never payload text."""
    client = QdrantClient(url="http://127.0.0.1:6333", timeout=10)
    query_filter = models.Filter(must=[
        models.FieldCondition(key="app_id", match=models.MatchValue(value=app_id)),
        models.FieldCondition(key="node_type", match=models.MatchValue(value="memory")),
    ])
    grouped = defaultdict(list)
    points, cursor = client.scroll(COLLECTION, scroll_filter=query_filter, limit=256,
                                   with_payload=["app_id", "node_type", "source_section"], with_vectors=False)
    if cursor is not None:
        raise RuntimeError("Memory scroll exceeded the expected candidate node count.")
    for point in points:
        section = (point.payload or {}).get("source_section")
        if section:
            grouped[section].append(str(point.id))
    return dict(grouped)


def main() -> None:
    app_id = str(uuid.UUID(os.environ.get("NEXPLY_APP_ID", "")))
    dataset = build_dataset(QUERY_SPECS, read_memory_ids(app_id))
    OUTPUT.write_text(json.dumps(dataset, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(dataset['queries'])} privacy-minimized, ID-annotated queries to {OUTPUT.name}.")


if __name__ == "__main__":
    main()
