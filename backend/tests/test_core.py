import json
from io import BytesIO
from unittest.mock import Mock

import pymupdf
import pytest
from docx import Document
from pydantic import ValidationError

from nexus.core import resume_extractor
from nexus.core.parser import extract_text
from nexus.core.schemas.resume import ResumeData
from nexus.api.routes.resumes import router as legacy_resumes_router


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


def test_extract_text_from_utf8_txt_with_bom():
    result = extract_text("resume.txt", b"\xef\xbb\xbfJordan Avery\r\nPython")

    assert result == "Jordan Avery\r\nPython"


def test_extract_text_from_docx_skips_blank_paragraphs():
    result = extract_text(
        "resume.docx",
        make_docx(["Jordan Avery", "  ", "Python developer"]),
    )

    assert result == "Jordan Avery\nPython developer"


def test_extract_text_from_pdf_preserves_page_markers():
    document = pymupdf.open()
    first = document.new_page()
    first.insert_text((72, 72), "Jordan Avery")
    second = document.new_page()
    second.insert_text((72, 72), "Python developer")
    content = document.tobytes()
    document.close()

    result = extract_text("resume.pdf", content)

    assert "--- Page 1 ---\nJordan Avery" in result
    assert "--- Page 2 ---\nPython developer" in result


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

    assert result["experience"][0]["achievements"] == ["Improved throughput by 20%"]
    assert result["experience"][0]["team_size"] == "6 engineers"
    assert result["additional_sections"][0]["details"] == ["Mentor"]
    assert result["additional_sections"][1]["title"] == "Patents"
    assert result["additional_sections"][1]["details"] == ["US-123"]


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
    assert result.experience[0].responsibilities == ["Built APIs", "Reduced latency"]


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
    assert request["json"]["options"]["num_predict"] > 0


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
