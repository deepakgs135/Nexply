"""Print aggregate candidate-memory diagnostics without exposing profile text."""

import os
import uuid
from collections import Counter

from nexus.storage.postgres import get_candidate_profile
from nexus.services.candidate_memory_builder import build_candidate_memories


def main() -> None:
    raw_id = os.environ.get("NEXPLY_APP_ID")
    if not raw_id:
        raise SystemExit("Set NEXPLY_APP_ID to a candidate app_id before inspection.")
    app_id = str(uuid.UUID(raw_id))
    profile = get_candidate_profile(app_id)
    if not profile:
        raise SystemExit("No candidate profile exists for the configured app_id.")
    memories = build_candidate_memories(profile)
    print(f"Generated memory count: {len(memories)}")
    for section, count in sorted(Counter(item["source_section"] for item in memories).items()):
        print(f"{section}: {count}")


if __name__ == "__main__":
    main()
