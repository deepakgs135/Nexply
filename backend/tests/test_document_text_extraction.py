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

def test_extract_text_includes_profile_urls_embedded_as_pdf_links():
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "LinkedIn")
    page.insert_link({
        "kind": pymupdf.LINK_URI,
        "from": pymupdf.Rect(68, 58, 120, 76),
        "uri": "https://www.linkedin.com/in/sample-candidate",
    })
    content = document.tobytes()
    document.close()

    result = extract_text("resume.pdf", content)

    assert "LinkedIn: https://www.linkedin.com/in/sample-candidate" in result
