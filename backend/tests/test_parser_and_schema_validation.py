import json

from io import BytesIO

from unittest.mock import Mock

import pymupdf

import pytest

from docx import Document

from pydantic import ValidationError

from nexus.core import resume_extractor

from nexus.core.prompts.resume_extraction import RESUME_EXTRACTION_PROMPT

from nexus.core.parser import extract_text

from nexus.core.schemas.resume import ResumeData

from nexus.api.routes.resumes import router as legacy_resumes_router

from nexus.services import resume_service

def make_pdf(text: str | None) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content

def make_docx(paragraphs: list[str]) -> bytes:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    output = BytesIO()
    document.save(output)
    return output.getvalue()

def test_extract_text_ignores_github_repository_links_as_profile_links():
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Project repository")
    page.insert_link({
        "kind": pymupdf.LINK_URI,
        "from": pymupdf.Rect(68, 58, 160, 76),
        "uri": "https://github.com/sample-candidate/resume-project",
    })
    content = document.tobytes()
    document.close()

    result = extract_text("resume.pdf", content)

    assert "Profile links:" not in result

def test_extract_text_rejects_textless_scanned_pdf():
    with pytest.raises(ValueError, match="No text was extracted"):
        extract_text("scanned.pdf", make_pdf(None))

def test_extract_text_rejects_empty_docx():
    with pytest.raises(ValueError, match="No text was extracted"):
        extract_text("empty.docx", make_docx(["  ", "\t"]))

def test_extract_text_rejects_unknown_extension():
    with pytest.raises(ValueError, match="Unsupported file format"):
        extract_text("resume.rtf", b"text")

def test_resume_schema_applies_empty_defaults():
    result = ResumeData.model_validate({"full_name": "Jordan Avery"})

    assert result.full_name == "Jordan Avery"
    assert result.skills == []
    assert result.education == []
    assert result.experience == []
    assert result.projects == []
    assert result.additional_sections == []

def test_resume_schema_requires_project_name():
    with pytest.raises(ValidationError):
        ResumeData.model_validate({"projects": [{}]})
