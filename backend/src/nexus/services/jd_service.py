
from nexus.storage.jd_repository import get_jd, update_jd


def get_jd_details(document_id: str) -> dict | None:
    """Retrieve a job description record by its ID."""
    return get_jd(document_id)


def save_parsed_jd(document_id: str, parsed_text: str) -> bool:
    """Save extracted job description text and update parsing status."""
    if not parsed_text or not parsed_text.strip():
        raise ValueError("Parsed job description text cannot be empty.")

    return update_jd(
        document_id,
        {
            "parsed_text": parsed_text,
            "parsing_status": "completed",
            "parsing_error": None,
        },
    )
