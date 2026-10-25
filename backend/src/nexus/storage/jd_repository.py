
from nexus.core.debug import debug_trace
from datetime import datetime, timezone

from bson import ObjectId

from nexus.storage.mongodb import job_descriptions


@debug_trace
def create_jd(record: dict) -> str:
    """Insert a job description document and return its ID."""
    result = job_descriptions.insert_one(record)
    return str(result.inserted_id)


@debug_trace
def get_jd(document_id: str, app_id: str) -> dict | None:
    """Retrieve a job description by its MongoDB ID."""
    if not ObjectId.is_valid(document_id):
        return None

    return job_descriptions.find_one({"_id": ObjectId(document_id), "app_id": str(app_id)})


@debug_trace
def update_jd(document_id: str, app_id: str, fields: dict) -> bool:
    """Update fields in a job description document."""
    if not ObjectId.is_valid(document_id):
        return False

    update_fields = {
        **fields,
        "updated_at": datetime.now(timezone.utc),
    }

    result = job_descriptions.update_one(
        {"_id": ObjectId(document_id), "app_id": str(app_id)},
        {"$set": update_fields},
    )

    return result.matched_count == 1
