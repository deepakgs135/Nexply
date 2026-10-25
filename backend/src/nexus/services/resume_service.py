
from nexus.core.debug import debug_trace
from nexus.storage.mongodb import file_bucket
from nexus.storage.resume_repository import get_resume, update_resume
from nexus.core.parser import extract_text
from nexus.core.resume_extractor import extract_resume_data


@debug_trace
def get_resume_details(document_id: str) -> dict | None:
    """Retrieve a resume record by its MongoDB ID."""
    return get_resume(document_id)


@debug_trace
def parse_resume(document_id: str) -> dict:
    """Read the original resume, extract text, and save it."""
    resume = get_resume(document_id)

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
            {
                "parsing_status": "failed",
                "parsing_error": str(exc),
            },
        )
        raise


@debug_trace
def extract_resume(document_id: str) -> dict:
    """Extract structured resume data using Ollama and save it."""
    resume = get_resume(document_id)

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

        return {
            "document_id": document_id,
            "llm_status": "completed",
            "structured_result": structured_result,
        }

    except Exception as exc:
        # Record failure so the client can inspect the current status.
        update_resume(
            document_id,
            {
                "llm_status": "failed",
                "llm_error": str(exc),
            },
        )
        raise
