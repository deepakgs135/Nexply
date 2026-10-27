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

def test_resume_extractor_reports_empty_truncated_output(monkeypatch):
    response = Mock()
    response.json.return_value = {
        "message": {"content": ""},
        "done_reason": "length",
    }
    monkeypatch.setattr(resume_extractor.requests, "post", Mock(return_value=response))

    with pytest.raises(ValueError, match="empty content.*length"):
        resume_extractor.extract_resume_data("Sample resume text")

def test_resume_extractor_reports_invalid_json(monkeypatch):
    response = Mock()
    response.json.return_value = {"message": {"content": "not json"}}
    monkeypatch.setattr(resume_extractor.requests, "post", Mock(return_value=response))

    with pytest.raises(ValueError, match="invalid JSON"):
        resume_extractor.extract_resume_data("Sample resume text")

def test_resume_extractor_reports_schema_path_without_echoing_content(monkeypatch):
    response = Mock()
    response.json.return_value = {
        "message": {"content": json.dumps({"projects": [{}]})}
    }
    monkeypatch.setattr(resume_extractor.requests, "post", Mock(return_value=response))

    with pytest.raises(ValueError, match=r"projects\.0\.name: missing"):
        resume_extractor.extract_resume_data("Sample resume text")

def test_resume_extractor_rejects_blank_input_without_calling_ollama(monkeypatch):
    post = Mock()
    monkeypatch.setattr(resume_extractor.requests, "post", post)

    with pytest.raises(ValueError, match="cannot be empty"):
        resume_extractor.extract_resume_data("  \n")

    post.assert_not_called()
