from nexus.core.debug import debug_trace
import logging

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from nexus.core.config import MAX_UPLOAD_SIZE_MB

from nexus.storage.mongodb import resumes, save_original_file
from nexus.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Resumes"])

ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}

MAX_FILE_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post("/upload", status_code=201)
@debug_trace
async def upload_resume(
    user: Annotated[dict, Depends(get_current_user)],
    file: UploadFile = File(...),
):
    filename = (file.filename or "").strip()

    extension = (
        "." + filename.rsplit(".", 1)[-1].lower()
        if "." in filename else ""
    )

    if extension not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Supported formats: PDF, DOCX, TXT.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Maximum file size is {MAX_UPLOAD_SIZE_MB} MB.",
        )

    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The file does not appear to be a valid PDF.",
        )

    if extension == ".docx" and not content.startswith(b"PK"):
        raise HTTPException(
            status_code=400,
            detail="The file does not appear to be a valid DOCX.",
        )

    try:
        logger.info(
            "Saving resume upload size_bytes=%s content_type=%s",
            len(content),
            ALLOWED_TYPES[extension],
        )
        document_id = save_original_file(
            filename=filename,
            content=content,
            content_type=ALLOWED_TYPES[extension],
            collection=resumes,
            app_id=user["app_id"],
        )
        logger.info("Resume upload saved successfully")
    except Exception as exc:
        logger.exception("Unable to store the uploaded resume")
        raise HTTPException(
            status_code=500,
            detail="Unable to store the uploaded resume.",
        ) from exc

    return {
        "document_id": document_id,
        "filename": filename,
        "size_bytes": len(content),
        "status": "uploaded",
        "parsing_status": "pending",
        "llm_status": "pending",
    }
