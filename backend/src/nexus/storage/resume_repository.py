
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
def list_resumes(app_id: str, skip: int = 0, limit: int = 50) -> list[dict]:
    """List a user's resume summaries without returning parsed source text."""
    projection = {
        "original_filename": 1,
        "original_size_bytes": 1,
        "created_at": 1,
        "updated_at": 1,
        "parsing_status": 1,
        "llm_status": 1,
        "structured_result.full_name": 1,
        "structured_result.professional_title": 1,
    }
    cursor = (
        resumes.find({"app_id": str(app_id)}, projection)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return list(cursor)


@debug_trace
def count_resumes(app_id: str) -> int:
    """Count only resumes owned by the authenticated user."""
    return resumes.count_documents({"app_id": str(app_id)})


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


@debug_trace
def delete_resume_record(document_id: str, app_id: str) -> bool:
    """Delete one resume metadata record only when it belongs to the user."""
    if not ObjectId.is_valid(document_id):
        return False
    result = resumes.delete_one({"_id": ObjectId(document_id), "app_id": str(app_id)})
    return result.deleted_count == 1
