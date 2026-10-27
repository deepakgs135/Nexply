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

def test_resume_extractor_normalizes_custom_section_details_to_strings():
    payload = resume_extractor.normalize_resume_payload({
        "additional_sections": [
            {"title": "Tools", "details": "MATLAB, Simulink, and CAN tools"},
            {"section_name": "Training", "content": {"course": "Safety systems", "year": 2025}},
        ],
    })
    result = ResumeData.model_validate(payload)

    assert result.additional_sections[0].details == ["MATLAB, Simulink, and CAN tools"]
    assert result.additional_sections[1].title == "Training"
    assert result.additional_sections[1].details == ['{"course": "Safety systems", "year": 2025}']

def test_extract_resume_mirrors_saved_mongo_profile_to_postgres(monkeypatch):
    record = {"parsed_text": "resume text", "original_filename": "resume.pdf"}
    profile = {"full_name": "Casey Rivera", "experience": [], "education": []}
    monkeypatch.setattr(resume_service, "get_resume", Mock(return_value=record))
    update = Mock(return_value=True)
    monkeypatch.setattr(resume_service, "update_resume", update)
    monkeypatch.setattr(resume_service, "extract_resume_data", Mock(return_value=profile))
    mirror = Mock()
    monkeypatch.setattr(resume_service.postgres, "upsert_candidate_profile", mirror)

    result = resume_service.extract_resume("mongo-document-id", "authenticated-app-id")

    assert result["sql_sync_status"] == "completed"
    mirror.assert_called_once_with("authenticated-app-id", "mongo-document-id", "resume.pdf", profile)

def test_resume_schema_retains_custom_details_and_nested_fields():
    payload = resume_extractor.normalize_resume_payload({
        "experience": [{
            "company": "Sample Labs",
            "achievements": ["Improved throughput by 20%"],
            "team_size": "6 engineers",
        }],
        "additional_sections": [{"title": "Community", "details": ["Mentor"]}],
        "patents": ["US-123"],
    })
    result = ResumeData.model_validate(payload).model_dump()

    assert result["experience"][0]["description"] == "<ul><li>Improved throughput by 20%</li></ul>"
    assert result["experience"][0]["achievements"] == []
    assert result["experience"][0]["team_size"] == "6 engineers"
    assert result["additional_sections"][0]["details"] == ["Mentor"]
    assert result["additional_sections"][1]["title"] == "Patents"
    assert result["additional_sections"][1]["details"] == ["US-123"]
