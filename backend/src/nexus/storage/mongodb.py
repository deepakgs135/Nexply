from bson import ObjectId
from nexus.core.debug import debug_trace
from nexus.storage.mongodb_runtime import client, db, file_bucket, job_descriptions, resumes
from nexus.storage.mongodb_upload import save_original_file as _save_original_file


@debug_trace
def save_original_file(
    filename: str,
    content: bytes,
    content_type: str,
    app_id: str,
    collection=None,
    upload_request_id: str | None = None,
) -> str:
    return _save_original_file(
        filename, content, content_type, app_id, collection, upload_request_id,
        bucket=file_bucket, default_collection=resumes,
    )


__all__ = ["ObjectId", "client", "db", "file_bucket", "job_descriptions", "resumes", "save_original_file"]
