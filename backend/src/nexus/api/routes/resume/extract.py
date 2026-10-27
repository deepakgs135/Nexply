
from nexus.core.debug import debug_trace
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from nexus.api.auth import get_current_user
from nexus.services.resume_service import CandidateProfileSyncError, extract_resume

router = APIRouter(tags=["Resumes"])


@router.post("/{document_id}/extract")
@debug_trace
def extract_resume_endpoint(document_id: str, user: Annotated[dict, Depends(get_current_user)]):
    """HTTP endpoint for structured resume extraction."""
    try:
        return extract_resume(document_id, user["app_id"])

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except CandidateProfileSyncError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Resume extraction failed.",
        ) from exc
