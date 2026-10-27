from datetime import datetime, timezone
import hashlib
from uuid import UUID

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from nexus.core.debug import debug_trace
from nexus.storage.mongodb_runtime import file_bucket, resumes

@debug_trace
def save_original_file(
    filename: str,
    content: bytes,
    content_type: str,
    app_id: str,
    collection=None,
    upload_request_id: str | None = None,
    *,
    bucket=file_bucket,
    default_collection=resumes,
) -> str:
    """Save an original file in GridFS and create its metadata record."""

    target_collection = default_collection if collection is None else collection
    now = datetime.now(timezone.utc)
    owner_id = str(app_id)
    content_sha256 = hashlib.sha256(content).hexdigest()
    request_key = str(UUID(upload_request_id)) if upload_request_id else None
    if request_key:
        # A stable ObjectId makes concurrent retries converge on one Mongo
        # record without adding a separate collection or a destructive migration.
        object_id_seed = hashlib.sha256(f"{owner_id}:{request_key}".encode("utf-8")).digest()
        document_id = ObjectId(object_id_seed[:12])
        existing = target_collection.find_one({"_id": document_id, "app_id": owner_id})
        if existing:
            if existing.get("upload_sha256") != content_sha256:
                raise ValueError("Idempotency key was already used for a different file.")
            return str(document_id)
    else:
        document_id = ObjectId()

    gridfs_file_id = bucket.upload_from_stream(
        filename,
        content,
        metadata={
            "document_id": str(document_id),
            "stage": "original",
            "content_type": content_type,
            "app_id": owner_id,
            "sha256": content_sha256,
            **({"upload_request_id": request_key} if request_key else {}),
        },
    )

    record = {
        "_id": document_id,
        "app_id": owner_id,
        "upload_sha256": content_sha256,
        **({"upload_request_id": request_key} if request_key else {}),
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
    except DuplicateKeyError:
        bucket.delete(gridfs_file_id)
        if request_key:
            existing = target_collection.find_one({"_id": document_id, "app_id": owner_id})
            if existing:
                if existing.get("upload_sha256") == content_sha256:
                    return str(document_id)
                raise ValueError("Idempotency key was already used for a different file.")
        raise
    except Exception:
        bucket.delete(gridfs_file_id)
        raise

    return str(document_id)
