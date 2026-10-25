
import os
from datetime import datetime, timezone

from bson import ObjectId
from gridfs import GridFSBucket
from pymongo import MongoClient


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://127.0.0.1:27017",
)

DATABASE_NAME = os.getenv("MONGODB_DATABASE", "nexply")

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000,
)

db = client[DATABASE_NAME]

# Main application collections
resumes = db["resume"]
job_descriptions = db["jd"]

# Original uploaded files
file_bucket = GridFSBucket(
    db,
    bucket_name="document_files",
)


def save_original_file(
    filename: str,
    content: bytes,
    content_type: str,
    collection=None,
) -> str:
    """Save an original file in GridFS and create its metadata record."""

    target_collection = resumes if collection is None else collection
    now = datetime.now(timezone.utc)
    document_id = ObjectId()

    print(
        "[DEBUG] Uploading original file to GridFS "
        f"filename={filename!r} bytes={len(content)} uri={MONGODB_URI} db={DATABASE_NAME}"
    )
    gridfs_file_id = file_bucket.upload_from_stream(
        filename,
        content,
        metadata={
            "document_id": str(document_id),
            "stage": "original",
            "content_type": content_type,
        },
    )

    record = {
        "_id": document_id,
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
        print(
            "[DEBUG] GridFS upload complete "
            f"file_id={gridfs_file_id} document_id={document_id}"
        )
        target_collection.insert_one(record)
        print(f"[DEBUG] Mongo insert complete document_id={document_id}")
    except Exception as exc:
        print(
            f"[DEBUG] Mongo insert failed, deleting GridFS file: "
            f"{type(exc).__name__}: {exc}"
        )
        file_bucket.delete(gridfs_file_id)
        raise

    return str(document_id)
