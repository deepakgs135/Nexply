from nexus.core.debug import debug_trace
from fastapi import APIRouter, HTTPException

from nexus.storage.mongodb import db

router = APIRouter(tags=["Health"])


@router.get("/health")
@debug_trace
def health():
    try:
        db.command("ping")
        return {
            "status": "ok",
            "database": db.name,
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed.",
        )