import logging
import traceback

from fastapi import APIRouter, File, HTTPException, UploadFile

from nexus.storage.mongodb import resumes, save_original_file

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Resumes"])

ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}

MAX_FILE_SIZE = 15 * 1024 * 1024


@router.post("/upload", status_code=201)
async def upload_resume(file: UploadFile = File(...)):
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
            detail="Maximum file size is 15 MB.",
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
            "Saving resume filename=%s size_bytes=%s content_type=%s",
            filename,
            len(content),
            ALLOWED_TYPES[extension],
        )
        document_id = save_original_file(
            filename=filename,
            content=content,
            content_type=ALLOWED_TYPES[extension],
            collection=resumes,
        )
        logger.info("Saved resume document_id=%s", document_id)
    except Exception as exc:
        logger.exception("Unable to store the uploaded resume")
        print(f"[DEBUG] Resume storage failed: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unable to store the uploaded resume: {type(exc).__name__}: {exc}",
        ) from exc

    return {
        "document_id": document_id,
        "filename": filename,
        "size_bytes": len(content),
        "status": "uploaded",
        "parsing_status": "pending",
        "llm_status": "pending",
    }
