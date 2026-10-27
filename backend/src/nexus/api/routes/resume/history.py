from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ValidationError
from psycopg.errors import UndefinedTable

from nexus.api.auth import get_current_user
from nexus.services.resume_service import get_latest_resume_for_owner, get_resume_details
from nexus.services.resume_service import delete_resume
from nexus.core.schemas.resume import ResumeData
from nexus.storage.resume_repository import update_resume
from nexus.core.resume_extractor import fill_experience_locations_from_source, normalize_resume_payload
from nexus.storage import postgres
import logging

router = APIRouter(tags=["Candidate Profile"])
logger = logging.getLogger(__name__)


class StructuredResultUpdate(BaseModel):
    structured_result: dict[str, Any]


class JobPreferences(BaseModel):
    current_ctc: str | None = None
    expected_ctc: str | None = None
    expected_ctc_range: str | None = None
    minimum_expected_ctc: str | None = None
    currency: str = "INR"
    preferred_locations: list[str] = Field(default_factory=list)
    preferred_job_titles: list[str] = Field(default_factory=list)
    work_mode: str | None = None
    employment_types: list[str] = Field(default_factory=list)
    notice_period: str | None = None
    availability: str | None = None
    willing_to_relocate: bool | None = None
    preferred_industries: list[str] = Field(default_factory=list)


class JobPreferencesUpdate(BaseModel):
    job_preferences: JobPreferences


@router.get("/latest")
def latest_resume_profile(user: Annotated[dict, Depends(get_current_user)]):
    """Return only the current profile and purge older resumes for this owner."""
    record = get_latest_resume_for_owner(user["app_id"])
    if record is None:
        return {"resume": None}
    structured_result = normalize_resume_payload(record.get("structured_result") or {}) if record.get("structured_result") else None
    if structured_result:
        fill_experience_locations_from_source(structured_result, record.get("parsed_text") or "")
    return {"resume": {
        "document_id": str(record.pop("_id")),
        "original_filename": record.get("original_filename"),
        "original_size_bytes": record.get("original_size_bytes"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
        "parsing_status": record.get("parsing_status"),
        "llm_status": record.get("llm_status"),
        "structured_result": structured_result,
    }}


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
    record = get_resume_details(document_id, user["app_id"])
    if record is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    try:
        normalized = normalize_resume_payload(payload.structured_result)
        fill_experience_locations_from_source(normalized, record.get("parsed_text") or "")
        profile = ResumeData.model_validate(normalized).model_dump(mode="json")
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    if not update_resume(document_id, user["app_id"], {"structured_result": profile, "llm_status": "completed", "llm_error": None}):
        raise HTTPException(status_code=404, detail="Resume not found.")
    return {"document_id": document_id, "structured_result": profile}


@router.get("/preferences")
def get_job_preferences(user: Annotated[dict, Depends(get_current_user)]):
    """Load preferences from PostgreSQL for the authenticated app_id."""
    try:
        preferences = postgres.get_job_preferences(user["app_id"])
    except UndefinedTable:
        logger.warning("Job preferences table is not installed; apply docs/sql/user_job_preferences.sql")
        return {"job_preferences": JobPreferences().model_dump(mode="json"), "configured": False}
    return {"job_preferences": preferences or JobPreferences().model_dump(mode="json"), "configured": True}


@router.put("/preferences")
def update_job_preferences(
    payload: JobPreferencesUpdate,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Save job preferences to PostgreSQL using the authenticated app_id."""
    preferences = payload.job_preferences.model_dump(mode="json")
    try:
        postgres.upsert_job_preferences(user["app_id"], preferences)
    except UndefinedTable as exc:
        raise HTTPException(status_code=503, detail="Preferences table is not installed. Run docs/sql/user_job_preferences.sql in the nexply database.") from exc
    return {"job_preferences": preferences}


@router.delete("/{document_id}", status_code=204)
def delete_resume_history_item(
    document_id: str,
    user: Annotated[dict, Depends(get_current_user)],
):
    """Delete the owner's resume record and its GridFS original files."""
    if not delete_resume(document_id, user["app_id"]):
        raise HTTPException(status_code=404, detail="Resume not found.")
