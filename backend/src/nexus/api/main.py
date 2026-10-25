from nexus.core.debug import debug_trace
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from nexus.core.config import APP_NAME

from nexus.api.routes.health import router as health_router
from nexus.api.routes.resume.upload import router as resume_upload_router
from nexus.api.routes.resume.parse import router as resume_parse_router
from nexus.api.routes.resume.extract import router as resume_extract_router
from nexus.api.routes.resume.get import router as resume_get_router
from nexus.core.config import BACKEND_ROOT, MAX_UPLOAD_SIZE_MB

FRONTEND_DIST = BACKEND_ROOT / "frontend" / "dist"

app = FastAPI(
    title=APP_NAME,
    description="Resume and job description processing API",
    version="1.0.0",
)
if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

app.include_router(health_router)

app.include_router(resume_upload_router, prefix="/resumes")
app.include_router(resume_parse_router, prefix="/resumes")
app.include_router(resume_extract_router, prefix="/resumes")
app.include_router(resume_get_router, prefix="/resumes")


@app.get("/")
@debug_trace
def root():
    index_file = FRONTEND_DIST / "index.html"
    if not index_file.is_file():
        return {
            "name": APP_NAME,
            "status": "running",
            "frontend": "Build the React app with `npm run build` in backend/frontend.",
            "docs": "/docs",
        }
    return FileResponse(index_file)


@app.get("/api/config")
@debug_trace
def ui_config():
    return {
        "max_upload_size_mb": MAX_UPLOAD_SIZE_MB,
        "supported_formats": [".pdf", ".docx", ".txt"],
    }


@app.get("/nexply.svg", include_in_schema=False)
@debug_trace
def favicon():
    return FileResponse(FRONTEND_DIST / "nexply.svg", media_type="image/svg+xml")
