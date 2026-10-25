from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ValidationError

from nexus.api.auth import get_current_user
from nexus.services.resume_service import get_resume_details
from nexus.services.resume_service import delete_resume
from nexus.storage.resume_repository import count_resumes, list_resumes
from nexus.core.schemas.resume import ResumeData
from nexus.storage.resume_repository import update_resume

router = APIRouter(tags=["Resume History"])


class StructuredResultUpdate(BaseModel):
    structured_result: dict[str, Any]


@router.get("/history")
def resume_history(
    user: Annotated[dict, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Return paginated resume summaries belonging only to this user."""
    app_id = user["app_id"]
    records = list_resumes(app_id, skip=skip, limit=limit)
    items = []
    for record in records:
        structured = record.get("structured_result") or {}
        items.append({
            "document_id": str(record.pop("_id")),
            "original_filename": record.get("original_filename"),
            "original_size_bytes": record.get("original_size_bytes"),
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            "parsing_status": record.get("parsing_status"),
            "llm_status": record.get("llm_status"),
            "candidate_name": structured.get("full_name"),
            "professional_title": structured.get("professional_title"),
        })
    return {
        "items": items,
        "total": count_resumes(app_id),
        "skip": skip,
        "limit": limit,
    }


@router.get("/{document_id}/profile")
def resume_history_profile(
    document_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Return one selected resume's structured result after owner verification."""
    record = get_resume_details(document_id, user["app_id"])
    if record is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return {
        "document_id": str(record["_id"]),
        "original_filename": record.get("original_filename"),
        "created_at": record.get("created_at"),
        "parsing_status": record.get("parsing_status"),
        "llm_status": record.get("llm_status"),
        "structured_result": record.get("structured_result"),
    }


@router.put("/{document_id}/structured-result")
def update_structured_result(
    document_id: str,
    payload: StructuredResultUpdate,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Update the selected user's existing resume profile in place."""
    try:
        profile = ResumeData.model_validate(payload.structured_result).model_dump(mode="json")
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    if not update_resume(document_id, user["app_id"], {"structured_result": profile, "llm_status": "completed", "llm_error": None}):
        raise HTTPException(status_code=404, detail="Resume not found.")
    return {"document_id": document_id, "structured_result": profile}


@router.delete("/{document_id}", status_code=204)
def delete_resume_history_item(
    document_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Delete the owner's resume record and its GridFS original files."""
    if not delete_resume(document_id, user["app_id"]):
        raise HTTPException(status_code=404, detail="Resume not found.")
