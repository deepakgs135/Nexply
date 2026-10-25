from fastapi import FastAPI

from nexus.api.routes.health import router as health_router
from nexus.api.routes.resume.upload import router as resume_upload_router
from nexus.api.routes.resume.parse import router as resume_parse_router
from nexus.api.routes.resume.extract import router as resume_extract_router
from nexus.api.routes.resume.get import router as resume_get_router

app = FastAPI(
    title="NEXPLY API",
    description="Resume and job description processing API",
    version="1.0.0",
)

app.include_router(health_router)

app.include_router(resume_upload_router, prefix="/resumes")
app.include_router(resume_parse_router, prefix="/resumes")
app.include_router(resume_extract_router, prefix="/resumes")
app.include_router(resume_get_router, prefix="/resumes")


@app.get("/")
def root():
    return {
        "name": "NEXPLY API",
        "status": "running",
        "docs": "/docs",
    }
