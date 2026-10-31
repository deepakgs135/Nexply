"""Load and validate candidate-specific relevance annotations."""

import json
from pathlib import Path
from typing import Any

from tests.retrieval_evaluation.query_catalog import QuerySpec

VALID_INTENTS = {
    "SKILL_SEARCH", "PROJECT_SEARCH", "EXPERIENCE_SEARCH", "EDUCATION_SEARCH",
    "CERTIFICATION_SEARCH", "SUMMARY_SEARCH", "AWARD_SEARCH", "PUBLICATION_SEARCH",
    "GENERAL_SEARCH",
}
VALID_SECTIONS = {
    "professional_summary", "skills", "experience", "projects", "education",
    "certifications", "awards", "publications", "additional_sections",
}


def build_dataset(specs: list[QuerySpec], ids_by_section: dict[str, list[str]]) -> dict[str, Any]:
    """Bind manually authored query scopes to actual memory IDs without copying text."""
    entries = []
    for spec in specs:
        if not spec.query.strip() or spec.intent not in VALID_INTENTS:
            raise ValueError(f"Invalid evaluation query: {spec.key}")
        if not spec.sections or not set(spec.sections) <= VALID_SECTIONS:
            raise ValueError(f"Invalid expected sections: {spec.key}")
        missing = [section for section in spec.sections if not ids_by_section.get(section)]
        if missing:
            raise ValueError(f"No indexed memories for {spec.key}: {', '.join(missing)}")
        relevant = sorted({memory_id for section in spec.sections for memory_id in ids_by_section[section]})
        entries.append({
            "query_id": spec.key, "query": spec.query, "category": spec.category,
            "expected_intent": spec.intent, "expected_source_sections": list(spec.sections),
            "relevant_memory_ids": relevant, "relevance_note": spec.rationale,
        })
    return {"dataset_version": 1, "queries": entries}


def load_dataset(path: Path, require_phase5_coverage: bool = True) -> list[dict[str, Any]]:
    """Read a JSON dataset and reject malformed or incomplete query records."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    queries = payload.get("queries") if isinstance(payload, dict) else None
    if not isinstance(queries, list) or not queries:
        raise ValueError("Evaluation dataset must contain a non-empty queries array.")
    required = {"query_id", "query", "category", "expected_intent", "expected_source_sections", "relevant_memory_ids", "relevance_note"}
    seen = set()
    for query in queries:
        if not isinstance(query, dict) or not required <= query.keys():
            raise ValueError("Each evaluation query must include all annotation fields.")
        if query["query_id"] in seen or query["expected_intent"] not in VALID_INTENTS:
            raise ValueError("Duplicate query ID or invalid expected intent in dataset.")
        if not isinstance(query["query"], str) or not query["query"].strip():
            raise ValueError("Evaluation queries cannot be empty.")
        if not set(query["expected_source_sections"]) <= VALID_SECTIONS:
            raise ValueError("Dataset contains an invalid expected source section.")
        if not isinstance(query["relevant_memory_ids"], list) or not query["relevant_memory_ids"]:
            raise ValueError("Each evaluation query needs at least one relevant memory ID.")
        seen.add(query["query_id"])
    if require_phase5_coverage:
        minimums = {"technical_skills": 6, "projects": 6, "work_experience": 6,
                    "education": 4, "certifications": 4, "general_profile": 5,
                    "multi_section": 5, "paraphrased_challenging": 4}
        counts = {category: sum(q["category"] == category for q in queries) for category in minimums}
        if len(queries) < 40 or any(counts[name] < minimum for name, minimum in minimums.items()):
            raise ValueError("Dataset does not meet the Phase 5 query-count and category minimums.")
    return queries
