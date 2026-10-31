
"""Qdrant indexing service for NEXPLY candidate memory trees."""

import uuid

from qdrant_client import QdrantClient, models

from nexus.services.embedding_service import generate_embeddings


QDRANT_URL = "http://127.0.0.1:6333"
COLLECTION_NAME = "candidate_memory_v1"

# Process nodes in small batches to control memory usage.
BATCH_SIZE = 10


def _validate_nodes(nodes: list[dict]) -> str:
    """Validate candidate tree nodes and return their shared app_id."""

    if not isinstance(nodes, list) or not nodes:
        raise ValueError("Candidate nodes must be a non-empty list.")

    app_ids = set()
    node_ids = set()

    for node in nodes:
        required_fields = {
            "node_id",
            "app_id",
            "node_type",
            "parent_id",
            "source_section",
            "memory_type",
            "source_index",
            "text",
            "child_count",
        }

        missing = required_fields - node.keys()

        if missing:
            raise ValueError(f"Missing node fields: {missing}")

        if not isinstance(node["text"], str) or not node["text"].strip():
            raise ValueError("Node text cannot be empty.")

        uuid.UUID(node["node_id"])
        uuid.UUID(str(node["app_id"]))

        app_ids.add(node["app_id"])
        node_ids.add(node["node_id"])

        if node["node_type"] not in {
            "candidate_root",
            "section",
            "memory",
        }:
            raise ValueError("Invalid node type.")

    if len(app_ids) != 1:
        raise ValueError("All nodes must belong to the same candidate.")

    if len(node_ids) != len(nodes):
        raise ValueError("Duplicate node IDs detected.")

    return next(iter(app_ids))



def index_candidate_tree(
    nodes: list[dict],
    dry_run: bool = True,
    batch_size: int = BATCH_SIZE,
) -> dict:
    """Generate embeddings and optionally upsert candidate nodes into Qdrant."""

    app_id = _validate_nodes(nodes)

    if batch_size < 1:
        raise ValueError("Batch size must be at least 1.")

    client = QdrantClient(url=QDRANT_URL)

    collection = client.get_collection(COLLECTION_NAME)
    vector_config = collection.config.params.vectors

    if vector_config.size != 768:
        raise ValueError(
            f"Expected 768-dimensional vectors, got {vector_config.size}."
        )

    indexed_count = 0
    validated_count = 0

    for start in range(0, len(nodes), batch_size):
        batch = nodes[start:start + batch_size]

        texts = [node["text"] for node in batch]
        vectors = generate_embeddings(texts)

        if len(vectors) != len(batch):
            raise ValueError("Embedding count does not match node count.")

        points = []

        for node, vector in zip(batch, vectors):

            if len(vector) != 768:
                raise ValueError(
                    f"Invalid vector dimensions for node {node['node_id']}."
                )

            if not all(
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and value == value
                and abs(value) != float("inf")
                for value in vector
            ):
                raise ValueError(
                    f"Invalid numeric embedding for node {node['node_id']}."
                )

            payload = {
                "app_id": str(node["app_id"]),
                "node_type": node["node_type"],
                "parent_id": node["parent_id"],
                "source_section": node["source_section"],
                "memory_type": node["memory_type"],
                "source_index": node["source_index"],
                "text": node["text"],
                "child_count": node["child_count"],
            }

            points.append(
                models.PointStruct(
                    id=node["node_id"],
                    vector=vector,
                    payload=payload,
                )
            )

        validated_count += len(points)

        if not dry_run:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points,
                wait=True,
            )
            indexed_count += len(points)

    return {
        "app_id": app_id,
        "collection": COLLECTION_NAME,
        "dry_run": dry_run,
        "validated_count": validated_count,
        "indexed_count": indexed_count,
        "batch_size": batch_size,
    }
