
"""Semantic retrieval service for NEXPLY candidate memories."""

import math
import uuid

from qdrant_client import QdrantClient, models

from nexus.services.embedding_service import generate_embedding
from nexus.services.candidate_llm_intent_classifier import (
    classify_candidate_query_with_llm,
)


QDRANT_URL = "http://127.0.0.1:6333"
COLLECTION_NAME = "candidate_memory_v1"
EMBEDDING_DIMENSIONS = 768

VALID_SECTIONS = {
    "professional_summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
    "awards",
    "publications",
    "additional_sections",
}


def search_candidate_memories(
    query: str,
    app_id: str,
    limit: int = 5,
    score_threshold: float | None = None,
    source_section: str | None = None,
) -> list[dict]:
    """
    Search candidate memories using LLM-assisted semantic retrieval.

    If source_section is provided, it takes priority.
    Otherwise, the LLM classifies the query and selects a section.
    The regex classifier is used automatically if Ollama fails.
    """

    # --------------------------------------------------
    # 1. Validate search query
    # --------------------------------------------------

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    query = query.strip()

    # --------------------------------------------------
    # 2. Validate candidate app_id
    # --------------------------------------------------

    try:
        candidate_id = str(uuid.UUID(str(app_id)))

    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Invalid candidate app_id.") from exc

    # --------------------------------------------------
    # 3. Validate result limit
    # --------------------------------------------------

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit < 1
    ):
        raise ValueError("Limit must be a positive integer.")

    # --------------------------------------------------
    # 4. Validate similarity threshold
    # --------------------------------------------------

    if score_threshold is not None:

        if (
            not isinstance(score_threshold, (int, float))
            or isinstance(score_threshold, bool)
            or not math.isfinite(score_threshold)
            or not 0 <= score_threshold <= 1
        ):
            raise ValueError(
                "Score threshold must be a finite number between 0 and 1."
            )

    # --------------------------------------------------
    # 5. Classify query or validate explicit section
    # --------------------------------------------------

    classification = None

    if source_section is None:

        classification = classify_candidate_query_with_llm(query)

        source_section = classification["source_section"]

    else:

        if not isinstance(source_section, str):
            raise ValueError("Source section must be a string.")

        source_section = source_section.strip().lower()

    if source_section is not None and source_section not in VALID_SECTIONS:
        raise ValueError(
            f"Invalid source section: {source_section}. "
            f"Allowed sections: {sorted(VALID_SECTIONS)}"
        )

    # --------------------------------------------------
    # 6. Generate query embedding
    # --------------------------------------------------

    query_vector = generate_embedding(query)

    if len(query_vector) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSIONS} embedding dimensions, "
            f"received {len(query_vector)}."
        )

    # --------------------------------------------------
    # 7. Connect to Qdrant
    # --------------------------------------------------

    client = QdrantClient(url=QDRANT_URL)

    # --------------------------------------------------
    # 8. Build candidate-specific filters
    # --------------------------------------------------

    conditions = [
        models.FieldCondition(
            key="app_id",
            match=models.MatchValue(value=candidate_id),
        ),
        models.FieldCondition(
            key="node_type",
            match=models.MatchValue(value="memory"),
        ),
    ]

    if source_section is not None:

        conditions.append(
            models.FieldCondition(
                key="source_section",
                match=models.MatchValue(value=source_section),
            )
        )

    query_filter = models.Filter(must=conditions)

    # --------------------------------------------------
    # 9. Perform semantic vector search
    # --------------------------------------------------

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
        score_threshold=score_threshold,
        with_payload=True,
        with_vectors=False,
    )

    # --------------------------------------------------
    # 10. Format search results
    # --------------------------------------------------

    results = []

    for point in response.points:

        payload = point.payload or {}

        results.append(
            {
                "memory_id": str(point.id),
                "score": float(point.score),
                "text": payload.get("text"),
                "source_section": payload.get("source_section"),
                "memory_type": payload.get("memory_type"),
                "source_index": payload.get("source_index"),
                "parent_id": payload.get("parent_id"),
            }
        )

    return results
