import re
from datetime import datetime, timezone
from typing import Annotated, Any, Literal

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError

from nexus.api.auth import get_current_user
from nexus.core.config import OLLAMA_RESUME_WRITER_MODEL
from nexus.core.schemas.resume import ResumeData
from nexus.services.resume_export import build_resume_docx
from nexus.services.resume_writer import available_resume_models, interview_resume_profile, rewrite_resume_text, write_resume
from nexus.services.resume_service import get_resume_details
from nexus.storage.resume_repository import create_resume


router = APIRouter(tags=["AI Resume"])


class AIResumeRequest(BaseModel):
    model: str | None = None
    target_job_description: str | None = Field(default=None, max_length=12000)


class ResumeExportRequest(BaseModel):
    structured_result: dict[str, Any]


class REXRewriteRequest(BaseModel):
    field_path: list[str | int]
    model: str | None = None
    style: Literal["concise", "brief", "detail", "elaborate"] = "brief"


class REXInterviewMessage(BaseModel):
    role: Literal["assistant", "user"]
    content: str = Field(min_length=1, max_length=5000)


class REXInterviewRequest(BaseModel):
    messages: list[REXInterviewMessage] = Field(min_length=1, max_length=40)
    current_profile: dict[str, Any] | None = None
    model: str | None = None


class ManualProfileSaveRequest(BaseModel):
    structured_result: dict[str, Any]


@router.post("/manual-profile/interview")
def rex_manual_profile_interview(
    payload: REXInterviewRequest,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Extract profile facts from a REX interview and ask the next follow-up question."""
    del user  # Auth is required; the transient interview itself is held by the authenticated client.
    try:
        return interview_resume_profile(
            [message.model_dump() for message in payload.messages],
            payload.current_profile,
            payload.model,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail="Ollama is unavailable. Start Ollama and try again.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/manual-profile")
def save_rex_manual_profile(
    payload: ManualProfileSaveRequest,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Create a user-owned, editable resume history record from a REX interview."""
    try:
        profile = ResumeData.model_validate(payload.structured_result).model_dump(mode="json")
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    if not any((profile.get("full_name"), profile.get("professional_summary"), profile.get("experience"), profile.get("education"), profile.get("skills"))):
        raise HTTPException(status_code=422, detail="Add at least one candidate detail before saving the profile.")
    now = datetime.now(timezone.utc)
    document_id = create_resume({
        "source": "rex_manual_profile",
        "original_filename": "Manually created profile · REX",
        "original_size_bytes": 0,
        "original_file_id": None,
        "parsed_text": None,
        "structured_result": profile,
        "parsing_status": "not_applicable",
        "llm_status": "completed",
        "parsing_error": None,
        "llm_error": None,
        "created_at": now,
        "updated_at": now,
    }, user["app_id"])
    return {"document_id": document_id, "structured_result": profile}


@router.get("/ai/models")
def resume_writer_models(user: Annotated[dict, Depends(get_current_user)]):
    """List locally installed Ollama text models for the AI resume writer."""
    try:
        models = available_resume_models()
        if not models:
            raise HTTPException(status_code=503, detail="No text-generation models are installed in Ollama.")
        default = OLLAMA_RESUME_WRITER_MODEL if OLLAMA_RESUME_WRITER_MODEL in models else models[0]
        return {"models": models, "default_model": default}
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail="Ollama is unavailable. Start Ollama and try again.") from exc


@router.post("/{document_id}/ai-resume")
def generate_ai_resume(
    document_id: str,
    payload: AIResumeRequest,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Generate a non-persisted resume draft from this owner's saved profile."""
    record = get_resume_details(document_id, user["app_id"])
    if record is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    profile = record.get("structured_result")
    if not profile:
        raise HTTPException(status_code=409, detail="Extract a structured profile before using REX.")
    try:
        models = available_resume_models()
        model = payload.model or (OLLAMA_RESUME_WRITER_MODEL if OLLAMA_RESUME_WRITER_MODEL in models else (models[0] if models else None))
        if not model:
            raise HTTPException(status_code=503, detail="No text-generation models are installed in Ollama.")
        generated = write_resume(profile, model, payload.target_job_description)
    except HTTPException:
        raise
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail="Ollama could not generate the resume. Check that it is running and try again.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"document_id": document_id, "model": model, "structured_result": generated}


@router.post("/{document_id}/rex/rewrite")
def rewrite_resume_field(
    document_id: str,
    payload: REXRewriteRequest,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Return a REX rewrite for one field; do not persist until the user saves."""
    record = get_resume_details(document_id, user["app_id"])
    if record is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    profile = record.get("structured_result")
    if not profile:
        raise HTTPException(status_code=409, detail="Extract a structured profile before using REX.")
    try:
        rewritten = rewrite_resume_text(profile, payload.field_path, payload.model, payload.style)
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail="Ollama is unavailable. Start Ollama and try again.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"document_id": document_id, **rewritten}


@router.post("/{document_id}/ai-resume/export")
def export_ai_resume(
    document_id: str,
    payload: ResumeExportRequest,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Download a generated resume as DOCX without storing another Mongo record."""
    if get_resume_details(document_id, user["app_id"]) is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    try:
        profile = ResumeData.model_validate(payload.structured_result).model_dump(mode="json")
        content = build_resume_docx(profile)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    base_name = re.sub(r"[^A-Za-z0-9_-]+", "-", profile.get("full_name") or "candidate-resume").strip("-") or "candidate-resume"
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{base_name[:80]}-resume.docx"'},
    )
