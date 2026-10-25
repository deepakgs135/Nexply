
from nexus.core.debug import debug_trace
from io import BytesIO
from pathlib import Path

import pymupdf
from docx import Document


@debug_trace
def extract_text(filename: str, content: bytes) -> str:
    """Extract text from PDF, DOCX, or TXT content."""
    extension = Path(filename).suffix.lower()
    has_extractable_text = False

    if extension == ".pdf":
        with pymupdf.open(stream=content, filetype="pdf") as pdf:
            pages = []

            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()
                has_extractable_text = has_extractable_text or bool(text)
                pages.append(f"--- Page {page_number} ---\n{text}")

            result = "\n\n".join(pages)

    elif extension == ".docx":
        document = Document(BytesIO(content))
        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]
        result = "\n".join(paragraphs)

    elif extension == ".txt":
        result = content.decode("utf-8-sig")

    else:
        raise ValueError("Unsupported file format for text extraction.")

    if not result.strip() or (extension == ".pdf" and not has_extractable_text):
        raise ValueError(
            "No text was extracted. The file may be empty or scanned."
        )

    return result
