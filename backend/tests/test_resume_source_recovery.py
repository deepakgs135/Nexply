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

def test_resume_extractor_fills_missing_literal_contact_values_from_text():
    result = resume_extractor.fill_contact_from_source(
        {"full_name": None, "email": None, "phone": None, "location": None},
        "Jordan Avery\nEmail: jordan.avery@example.com\nPhone: 555-010-2048\nLocation: Portland, Oregon",
    )

    assert result["full_name"] == "Jordan Avery"
    assert result["email"] == "jordan.avery@example.com"
    assert result["phone"] == "555-010-2048"
    assert result["location"] == "Portland, Oregon"

def test_resume_extractor_fills_missing_experience_end_date_from_source():
    result = resume_extractor.fill_experience_dates_from_source(
        {"experience": [{
            "job_title": "Junior Developer", "company": "Sample Labs",
            "start_date": "June 2024", "end_date": None,
        }]},
        "Junior Developer, Sample Labs, June 2024 - Present",
    )

    assert result["experience"][0]["end_date"] == "Present"

def test_resume_extractor_fills_clickable_profile_links_from_source():
    result = resume_extractor.fill_profile_links_from_source(
        {"websites": []},
        "School: https://www.cit.edu.in\n"
        "Profile links:\n"
        "LinkedIn: https://linkedin.com/in/sample\n"
        "GitHub: https://github.com/sample\n"
        "LeetCode: https://leetcode.com/sample\n"
        "Portfolio: https://sample-portfolio.lovable.app\n"
        "Project repository: https://github.com/sample/project",
    )

    assert [value.split(": ", 1)[0] for value in result["websites"]] == [
        "LinkedIn", "GitHub", "LeetCode", "Portfolio",
    ]
    assert all("https://" in value for value in result["websites"])
