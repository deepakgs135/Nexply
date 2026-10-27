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

def test_resume_extractor_normalizes_common_alternate_llm_keys():
    payload = resume_extractor.normalize_resume_payload({
        "name": {"first_name": "Jordan", "last_name": "Avery"},
        "contact_info": {"email": "jordan@example.com"},
        "skills_list": ["Python", "FastAPI"],
        "experience_list": [{
            "title": "Developer", "company": "Sample Labs",
            "responsibilities": ["Built APIs"],
            "start_date_string": "June 2024",
            "responsibilities_and_results": ["Built APIs", "Reduced latency"],
        }],
    })
    result = ResumeData.model_validate(payload)

    assert result.full_name == "Jordan Avery"
    assert result.email == "jordan@example.com"
    assert result.skills == ["Python", "FastAPI"]
    assert result.experience[0].job_title == "Developer"
    assert result.experience[0].start_date == "June 2024"
    assert result.experience[0].description == "<ul><li>Built APIs</li><li>Reduced latency</li></ul>"
    assert result.experience[0].responsibilities == []

def test_resume_extractor_recovers_bullets_from_malformed_experience_keys():
    payload = resume_extractor.normalize_resume_payload({
        "experience": [
            {"job_title": "Engineer", "company": "Example", "location null, description": ["First bullet", "Second bullet"]},
            {"job_title": "Analyst", "company": "Sample", "description null, description": ["Third bullet"]},
        ],
    })

    assert payload["experience"][0]["description"] == "<ul><li>First bullet</li><li>Second bullet</li></ul>"
    assert payload["experience"][0]["responsibilities"] == []
    assert "location null, description" not in payload["experience"][0]
    assert payload["experience"][1]["description"] == "<ul><li>Third bullet</li></ul>"
    assert "description null, description" not in payload["experience"][1]

def test_resume_extractor_recovers_experience_locations_and_bullets_from_saved_model_aliases():
    payload = resume_extractor.normalize_resume_payload({
        "experience": [
            {"job_title": "Engineer", "location": None, "location_string": "Coimbatore", "responsibilities": [], "responsibilities_and_achievements": ["Built systems"]},
        ],
    })

    assert payload["experience"][0]["location"] == "Coimbatore"
    assert payload["experience"][0]["description"] == "<ul><li>Built systems</li></ul>"
    assert payload["experience"][0]["responsibilities"] == []
