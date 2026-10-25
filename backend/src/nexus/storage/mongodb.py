
from datetime import datetime, timezone

from nexus.core.debug import debug_trace

from bson import ObjectId
from gridfs import GridFSBucket
from pymongo import MongoClient

from nexus.core.config import (
    MONGODB_DATABASE,
    MONGODB_GRIDFS_BUCKET,
    MONGODB_JD_COLLECTION,
    MONGODB_RESUME_COLLECTION,
    MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    MONGODB_URI,
)


client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
)

db = client[MONGODB_DATABASE]

# Main application collections
resumes = db[MONGODB_RESUME_COLLECTION]
job_descriptions = db[MONGODB_JD_COLLECTION]

# Original uploaded files
file_bucket = GridFSBucket(
    db,
    bucket_name=MONGODB_GRIDFS_BUCKET,
)


@debug_trace
def save_original_file(
    filename: str,
    content: bytes,
    content_type: str,
    app_id: str,
    collection=None,
) -> str:
    """Save an original file in GridFS and create its metadata record."""

    target_collection = resumes if collection is None else collection
    now = datetime.now(timezone.utc)
    document_id = ObjectId()

    gridfs_file_id = file_bucket.upload_from_stream(
        filename,
        content,
        metadata={
            "document_id": str(document_id),
            "stage": "original",
            "content_type": content_type,
            "app_id": str(app_id),
        },
    )

    record = {
        "_id": document_id,
        "app_id": str(app_id),
        "original_file_id": gridfs_file_id,
        "original_filename": filename,
        "original_content_type": content_type,
        "original_size_bytes": len(content),
        "parsed_text": None,
        "structured_result": None,
        "parsing_status": "pending",
        "llm_status": "pending",
        "created_at": now,
        "updated_at": now,
    }

    try:
        target_collection.insert_one(record)
    except Exception:
        file_bucket.delete(gridfs_file_id)
        raise

    return str(document_id)
