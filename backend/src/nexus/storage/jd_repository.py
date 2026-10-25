
from nexus.core.debug import debug_trace
from datetime import datetime, timezone

from bson import ObjectId

from nexus.storage.mongodb import job_descriptions


@debug_trace
def create_jd(record: dict, app_id: str) -> str:
    """Insert a job description owned by the authenticated PostgreSQL app_id."""
    owned_record = {**record, "app_id": str(app_id)}
    result = job_descriptions.insert_one(owned_record)
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
    if "_id" in fields or "app_id" in fields:
        raise ValueError("Job-description identity and ownership fields cannot be changed.")

    update_fields = {
        **fields,
        "updated_at": datetime.now(timezone.utc),
    }

    result = job_descriptions.update_one(
        {"_id": ObjectId(document_id), "app_id": str(app_id)},
        {"$set": update_fields},
    )

    return result.matched_count == 1
