
from nexus.core.debug import debug_trace
from nexus.storage.mongodb import file_bucket
from nexus.storage.resume_repository import delete_resume_record, get_latest_resume, get_resume, list_other_resume_ids, update_resume
from gridfs.errors import NoFile
from nexus.core.parser import extract_text
from nexus.core.resume_extractor import extract_resume_data
from nexus.storage import postgres


class CandidateProfileSyncError(RuntimeError):
    """Mongo profile was saved, but its PostgreSQL mirror could not be updated."""


@debug_trace
def sync_candidate_profile_to_sql(
    document_id: str,
    app_id: str,
    filename: str | None,
    structured_result: dict,
) -> None:
    """Keep one SQL candidate_profiles row aligned with the user's Mongo profile."""
    try:
        postgres.upsert_candidate_profile(app_id, document_id, filename, structured_result)
    except Exception as exc:
        update_resume(document_id, app_id, {
            "sql_sync_status": "failed",
            "sql_sync_error": "PostgreSQL profile synchronization failed.",
        })
        raise CandidateProfileSyncError("MongoDB saved the profile, but PostgreSQL synchronization failed.") from exc
    update_resume(document_id, app_id, {"sql_sync_status": "completed", "sql_sync_error": None})


@debug_trace
def get_resume_details(document_id: str, app_id: str) -> dict | None:
    """Retrieve a resume record by its MongoDB ID."""
    return get_resume(document_id, app_id)


@debug_trace
def delete_resume(document_id: str, app_id: str) -> bool:
    """Delete the owner's resume record and every GridFS original tied to it."""
    resume = get_resume(document_id, app_id)
    if resume is None:
        return False

    file_ids = set()
    if resume.get("original_file_id"):
        file_ids.add(resume["original_file_id"])

    # Also clean up any duplicate original upload associated with this resume.
    # Ownership metadata constrains the broader cleanup query.
    for grid_file in file_bucket.find({
        "metadata.document_id": document_id,
        "metadata.app_id": str(app_id),
    }):
        file_ids.add(grid_file._id)

    for file_id in file_ids:
        try:
            file_bucket.delete(file_id)
        except NoFile:
            # An already-missing GridFS file does not prevent record cleanup.
            pass

    return delete_resume_record(document_id, app_id)


@debug_trace
def retain_latest_resume(app_id: str, keep_document_id: str) -> int:
    """Remove all older owner records and their GridFS objects."""
    removed = 0
    for document_id in list_other_resume_ids(app_id, keep_document_id):
        if delete_resume(document_id, app_id):
            removed += 1
    return removed


@debug_trace
def get_latest_resume_for_owner(app_id: str) -> dict | None:
    """Return the newest profile and clean up any pre-existing history."""
    record = get_latest_resume(app_id)
    if record is None:
        return None
    document_id = str(record["_id"])
    retain_latest_resume(app_id, document_id)
    return record


@debug_trace
def parse_resume(document_id: str, app_id: str) -> dict:
    """Read the original resume, extract text, and save it."""
    resume = get_resume(document_id, app_id)

    if resume is None:
        raise LookupError("Resume not found.")

    try:
        file_id = resume.get("original_file_id")
        filename = resume.get("original_filename")

        if not file_id or not filename:
            raise ValueError(
                "Original resume file information is missing."
            )

        # Download the original file from GridFS.
        with file_bucket.open_download_stream(file_id) as stream:
            file_content = stream.read()

        # Extract text from PDF, DOCX, or TXT.
        parsed_text = extract_text(filename, file_content)

        # Save parsed text in the same MongoDB document.
        updated = update_resume(
            document_id,
            app_id,
            {
                "parsed_text": parsed_text,
                "parsing_status": "completed",
                "parsing_error": None,
            },
        )

        if not updated:
            raise LookupError(
                "Resume record disappeared during parsing."
            )

        return {
            "document_id": document_id,
            "filename": filename,
            "parsing_status": "completed",
            "character_count": len(parsed_text),
        }

    except Exception as exc:
        update_resume(
            document_id,
            app_id,
            {
                "parsing_status": "failed",
                "parsing_error": str(exc),
            },
        )
        raise


@debug_trace
def extract_resume(document_id: str, app_id: str) -> dict:
    """Extract structured resume data using Ollama and save it."""
    resume = get_resume(document_id, app_id)

    if resume is None:
        raise LookupError("Resume not found.")

    parsed_text = resume.get("parsed_text")

    if not parsed_text or not parsed_text.strip():
        raise ValueError(
            "Parse the resume before extracting structured data."
        )

    # Mark extraction as in progress.
    update_resume(
        document_id,
        app_id,
        {
            "llm_status": "processing",
            "llm_error": None,
        },
    )

    try:
        # Call the core extractor; it validates the LLM output.
        structured_result = extract_resume_data(parsed_text)

        # Save the validated JSON in the existing resume record.
        updated = update_resume(
            document_id,
            app_id,
            {
                "structured_result": structured_result,
                "llm_status": "completed",
                "llm_error": None,
            },
        )

        if not updated:
            raise LookupError(
                "Resume record disappeared during extraction."
            )
    except Exception as exc:
        # Record failure so the client can inspect the current status.
        update_resume(
            document_id,
            app_id,
            {
                "llm_status": "failed",
                "llm_error": str(exc),
            },
        )
        raise

    sync_candidate_profile_to_sql(
        document_id,
        app_id,
        resume.get("original_filename"),
        structured_result,
    )
    return {
        "document_id": document_id,
        "llm_status": "completed",
        "structured_result": structured_result,
        "sql_sync_status": "completed",
    }
