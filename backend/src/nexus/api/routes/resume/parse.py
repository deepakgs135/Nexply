from fastapi import APIRouter, HTTPException

from nexus.services.resume_service import parse_resume

router = APIRouter(tags=["Resumes"])


@router.post("/{document_id}/parse")
def parse_resume_endpoint(document_id: str):
    try:
        return parse_resume(document_id)

    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Resume parsing failed.",
        ) from exc
