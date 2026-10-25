
from datetime import datetime, timezone

from nexus.core.debug import debug_trace
from bson import ObjectId
from fastapi import APIRouter, File, HTTPException, UploadFile
from gridfs.errors import NoFile

from nexus.storage.mongodb import resumes, file_bucket, save_original_file
from nexus.core.parser import extract_text

router = APIRouter(prefix="/resumes", tags=["Resumes"])

ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}

MAX_FILE_SIZE = 15 * 1024 * 1024


@router.post("/upload", status_code=201)
@debug_trace
async def upload_resume(file: UploadFile = File(...)):
    filename = (file.filename or "").strip()
    extension = (
        "." + filename.rsplit(".", 1)[-1].lower()
        if "." in filename else ""
    )

    if extension not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Supported file formats: PDF, DOCX, TXT.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Maximum file size is 15 MB.")

    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")

    if extension == ".docx" and not content.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="Invalid DOCX file.")

    try:
        document_id = save_original_file(
            filename=filename,
            content=content,
            content_type=ALLOWED_TYPES[extension],
            collection=resumes,
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to store the uploaded resume.",
        )

    return {
        "document_id": document_id,
        "filename": filename,
        "size_bytes": len(content),
        "status": "uploaded",
        "parsing_status": "pending",
        "llm_status": "pending",
    }


@router.post("/{document_id}/parse")
@debug_trace
def parse_resume(document_id: str):
    if not ObjectId.is_valid(document_id):
        raise HTTPException(status_code=400, detail="Invalid document ID.")

    oid = ObjectId(document_id)
    record = resumes.find_one({"_id": oid})

    if not record:
        raise HTTPException(status_code=404, detail="Resume not found.")

    original_file_id = record.get("original_file_id")
    if not original_file_id:
        raise HTTPException(status_code=409, detail="Original file reference is missing.")

    try:
        with file_bucket.open_download_stream(original_file_id) as stream:
            original_content = stream.read()
        original_filename = record["original_filename"]
    except NoFile:
        raise HTTPException(status_code=404, detail="Original file not found in GridFS.")

    resumes.update_one(
        {"_id": oid},
        {"$set": {
            "parsing_status": "processing",
            "updated_at": datetime.now(timezone.utc),
        }},
    )

    try:
        parsed_text = extract_text(original_filename, original_content)

        resumes.update_one(
            {"_id": oid},
            {"$set": {
                "parsed_text": parsed_text,
                "parsed_text_characters": len(parsed_text),
                "parsing_status": "completed",
                "updated_at": datetime.now(timezone.utc),
            },
             "$unset": {"parsing_error": ""}},
        )
    except Exception as exc:
        resumes.update_one(
            {"_id": oid},
            {"$set": {
                "parsing_status": "failed",
                "parsing_error": str(exc)[:500],
                "updated_at": datetime.now(timezone.utc),
            }},
        )
        raise HTTPException(
            status_code=422,
            detail=f"Resume parsing failed: {str(exc)[:300]}",
        )

    return {
        "document_id": str(oid),
        "original_filename": original_filename,
        "characters_extracted": len(parsed_text),
        "parsing_status": "completed",
        "storage": "nexply.resume.parsed_text",
    }
