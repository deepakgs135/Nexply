"""Run live retrieval evaluation; candidate scope comes only from the environment."""

import argparse
import os
import uuid
from pathlib import Path
from unittest.mock import patch

from qdrant_client import QdrantClient

from nexus.services import candidate_memory_retriever as retriever_service
from nexus.services.candidate_llm_intent_classifier import classify_candidate_query_with_llm
from tests.retrieval_evaluation.dataset import load_dataset
from tests.retrieval_evaluation.evaluation_runner import evaluate_queries
from tests.retrieval_evaluation.report_writer import write_reports
from tests.retrieval_evaluation.scope_validation import COLLECTION, QDRANT_URL, validate_label_ownership

DATASET = Path(__file__).with_name("test_queries.json")
OUTPUT_DIR = Path(__file__).parents[2] / "docs" / "retrieval_evaluation" / "reports"


def _live_retrieve(query: str, app_id: str, limit: int, classification: dict):
    """Reuse one measured classifier result and fetch the unthresholded top-N list."""
    with patch.object(retriever_service, "classify_candidate_query_with_llm", return_value=classification):
        return retriever_service.search_candidate_memories(query, app_id, limit=limit)


def _metadata() -> dict:
    collection = QdrantClient(url=QDRANT_URL, timeout=10).get_collection(COLLECTION)
    return {"qdrant_collection": COLLECTION, "qdrant_status": collection.status.value,
            "qdrant_points": collection.points_count,
            "vector_dimensions": collection.config.params.vectors.size,
            "distance": collection.config.params.vectors.distance.value,
            "classifier_model": "qwen3.5:9b", "embedding_model": "nomic-embed-text:latest"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="baseline", help="Report label, e.g. baseline or after")
    parser.add_argument("--k", nargs="+", type=int, default=[1, 3, 5, 10])
    parser.add_argument("--thresholds", nargs="+", default=["none", "0.2", "0.4", "0.6"])
    args = parser.parse_args()
    raw_app_id = os.environ.get("NEXPLY_APP_ID")
    if not raw_app_id:
        raise SystemExit("Set NEXPLY_APP_ID to the authenticated candidate app_id before evaluation.")
    app_id = str(uuid.UUID(raw_app_id))
    queries = load_dataset(DATASET)
    validate_label_ownership(app_id, {item for q in queries for item in q["relevant_memory_ids"]})
    thresholds = tuple(None if value.lower() == "none" else float(value) for value in args.thresholds)
    report = evaluate_queries(queries, app_id, classify_candidate_query_with_llm,
                             _live_retrieve, args.k, thresholds,
                             progress=lambda done, total: print(f"Evaluated {done}/{total} queries.", flush=True))
    paths = write_reports(report, OUTPUT_DIR, args.name, _metadata())
    print(f"Evaluation complete for {report['query_count']} queries; reports written: {paths[0].name}, {paths[1].name}")


if __name__ == "__main__":
    main()
