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

def test_resume_extractor_maps_education_aliases_to_canonical_fields():
    payload = resume_extractor.normalize_resume_payload({
        "education": [{
            "degree": "B.Tech Artificial Intelligence And Data Science",
            "institution": "Coimbatore Institute of Technology",
            "start_date": None,
            "start_date_string": "10/2021",
            "end_date_string": "05/2025",
            "location_string": "Coimbatore, India",
            "honors_or_awards": "CGPA:7.7",
        }],
        "additional_sections": [
            {"title": "PATENT", "details": ["Patent details"]},
            {"title": "GAMES", "details": ["Games details"]},
        ],
    })
    education = ResumeData.model_validate(payload).model_dump()["education"][0]

    assert education["start_date"] == "10/2021"
    assert education["end_date"] == "05/2025"
    assert education["location"] == "Coimbatore, India"
    assert education["cgpa_or_percentage"] == "CGPA:7.7"
    assert not {"start_date_string", "end_date_string", "location_string", "honors_or_awards"}.intersection(education)
    assert [section["title"] for section in payload["additional_sections"]] == ["PATENT", "GAMES"]
