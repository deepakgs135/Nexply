from io import BytesIO
from docx import Document
from nexus.core.debug import debug_trace
from nexus.core.schemas.resume import ResumeData
from nexus.services.resume_docx_additional import render_additional
from nexus.services.resume_docx_header import configure_document, render_header
from nexus.services.resume_docx_projects import render_custom_sections, render_projects
from nexus.services.resume_docx_sections import render_education, render_experience, render_skills, render_summary


@debug_trace
def build_resume_docx(profile: dict) -> bytes:
    """Render a validated profile through focused DOCX section renderers."""
    data = ResumeData.model_validate(profile).model_dump(mode="json")
    document = Document()
    configure_document(document)
    render_header(document, data)
    render_summary(document, data)
    render_experience(document, data["experience"])
    render_skills(document, data)
    render_education(document, data["education"])
    render_projects(document, data["projects"])
    render_additional(document, data)
    render_custom_sections(document, data["additional_sections"])
    output = BytesIO()
    document.save(output)
    return output.getvalue()
