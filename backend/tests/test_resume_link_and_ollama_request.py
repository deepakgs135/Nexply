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

def test_resume_extractor_normalizes_website_alias_dictionary():
    result = resume_extractor.normalize_resume_payload({
        "social_links": {
            "linkedin": "https://linkedin.com/in/sample",
            "github": "https://github.com/sample",
        },
    })

    assert result["websites"] == [
        "Linkedin: https://linkedin.com/in/sample",
        "Github: https://github.com/sample",
    ]

def test_legacy_resume_route_module_imports():
    paths = {route.path for route in legacy_resumes_router.routes}

    assert "/resumes/upload" in paths
    assert "/resumes/{document_id}/parse" in paths

def test_resume_extractor_sends_constrained_non_thinking_request(monkeypatch):
    payload = {"full_name": "Jordan Avery", "skills": ["Python"]}
    response = Mock()
    response.json.return_value = {
        "message": {"content": json.dumps(payload)},
        "done_reason": "stop",
    }
    post = Mock(return_value=response)
    monkeypatch.setattr(resume_extractor.requests, "post", post)

    result = resume_extractor.extract_resume_data("Jordan Avery, Python developer")

    assert result["full_name"] == "Jordan Avery"
    assert result["skills"] == ["Python"]
    response.raise_for_status.assert_called_once_with()
    request = post.call_args.kwargs
    assert request["json"]["think"] is False
    assert request["json"]["format"] == ResumeData.model_json_schema()
    assert request["json"]["messages"][0]["content"] == RESUME_EXTRACTION_PROMPT
    assert request["json"]["options"]["num_predict"] > 0
