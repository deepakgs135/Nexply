
from nexus.core.debug import debug_trace
from datetime import datetime, timezone

from bson import ObjectId

from nexus.storage.mongodb import resumes


@debug_trace
def create_resume(record: dict, app_id: str) -> str:
    """Insert a resume owned by the authenticated PostgreSQL app_id."""
    owned_record = {**record, "app_id": str(app_id)}
    result = resumes.insert_one(owned_record)
    return str(result.inserted_id)


@debug_trace
def get_resume(document_id: str, app_id: str) -> dict | None:
    """Find a resume by its MongoDB document ID."""
    if not ObjectId.is_valid(document_id):
        return None

    return resumes.find_one({"_id": ObjectId(document_id), "app_id": str(app_id)})


@debug_trace
def update_resume(document_id: str, app_id: str, fields: dict) -> bool:
    """Update fields on an existing resume record."""
    if not ObjectId.is_valid(document_id):
        return False
    if "_id" in fields or "app_id" in fields:
        raise ValueError("Resume identity and ownership fields cannot be changed.")

    update_fields = {**fields, "updated_at": datetime.now(timezone.utc)}

    result = resumes.update_one(
        {"_id": ObjectId(document_id), "app_id": str(app_id)},
        {"$set": update_fields},
    )

    return result.matched_count == 1
