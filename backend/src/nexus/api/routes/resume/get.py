
from fastapi import APIRouter, HTTPException

from nexus.services.resume_service import get_resume_details

router = APIRouter(tags=["Resumes"])


@router.get("/{document_id}")
def get_resume_endpoint(document_id: str):
    """Retrieve resume metadata and extraction results."""
    resume = get_resume_details(document_id)

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found.",
        )

    # Convert MongoDB's ObjectId to a JSON-compatible string.
    resume["document_id"] = str(resume.pop("_id"))

    # Do not expose the internal GridFS file identifier.
    resume.pop("original_file_id", None)

    return resume
