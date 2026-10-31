
"""Build a hierarchical candidate memory tree for NEXPLY."""

import uuid
from collections import defaultdict

from nexus.services.candidate_memory_builder import (
    build_candidate_memories,
)


def _make_node_id(app_id: str, node_key: str) -> str:
    """Generate a deterministic UUID for a tree node."""

    raw = f"nexply:candidate-tree:{app_id}:{node_key}"

    return str(
        uuid.uuid5(uuid.NAMESPACE_URL, raw)
    )


def build_candidate_tree(profile: dict) -> list[dict]:
    """
    Build a three-level candidate memory tree.

    Level 1: Candidate root
    Level 2: Profile sections
    Level 3: Individual memory chunks

    Returns a flat list of nodes connected through parent_id.
    """

    app_id = profile.get("app_id")

    if not app_id:
        raise ValueError(
            "Candidate profile must contain app_id."
        )

    # Generate the existing memory chunks.
    memories = build_candidate_memories(profile)

    if not memories:
        raise ValueError(
            "No candidate memories were generated."
        )

    # Group memories by their original profile section.
    grouped_memories = defaultdict(list)

    for memory in memories:
        grouped_memories[memory["source_section"]].append(
            memory
        )

    # Level 1: Candidate root.
    root_id = _make_node_id(
        app_id,
        "candidate_root",
    )

    summary = profile.get("professional_summary") or ""

    root_text = (
        f"Candidate professional profile. {summary}"
    ).strip()

    nodes = []

    nodes.append({
        "node_id": root_id,
        "app_id": app_id,
        "node_type": "candidate_root",
        "parent_id": None,
        "source_section": None,
        "memory_type": None,
        "source_index": None,
        "text": root_text,
        "child_count": len(grouped_memories),
    })

    # Level 2: Section nodes.
    for source_section, section_memories in grouped_memories.items():

        section_id = _make_node_id(
            app_id,
            f"section:{source_section}",
        )

        # Build a semantic description from child memories.
        section_text = " ".join(
            memory["text"]
            for memory in section_memories
        )

        nodes.append({
            "node_id": section_id,
            "app_id": app_id,
            "node_type": "section",
            "parent_id": root_id,
            "source_section": source_section,
            "memory_type": None,
            "source_index": None,
            "text": (
                f"Candidate {source_section.replace('_', ' ')}. "
                f"{section_text}"
            ),
            "child_count": len(section_memories),
        })

        # Level 3: Individual memory nodes.
        for memory in section_memories:

            nodes.append({
                "node_id": memory["memory_id"],
                "app_id": app_id,
                "node_type": "memory",
                "parent_id": section_id,
                "source_section": memory["source_section"],
                "memory_type": memory["memory_type"],
                "source_index": memory["source_index"],
                "text": memory["text"],
                "child_count": 0,
            })

    # Validate unique node IDs.
    node_ids = [
        node["node_id"]
        for node in nodes
    ]

    if len(node_ids) != len(set(node_ids)):
        raise ValueError(
            "Duplicate node IDs detected in candidate tree."
        )

    # Validate that every non-root node has an existing parent.
    node_id_set = set(node_ids)

    for node in nodes:
        if node["node_type"] == "candidate_root":
            if node["parent_id"] is not None:
                raise ValueError(
                    "Candidate root cannot have a parent."
                )
        elif node["parent_id"] not in node_id_set:
            raise ValueError(
                f"Missing parent for node: {node['node_id']}"
            )

    # Validate that there is exactly one root.
    root_count = sum(
        node["node_type"] == "candidate_root"
        for node in nodes
    )

    if root_count != 1:
        raise ValueError(
            f"Expected one candidate root, found {root_count}."
        )

    return nodes
