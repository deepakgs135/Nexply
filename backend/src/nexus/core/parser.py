
from io import BytesIO
from pathlib import Path

import pymupdf
from docx import Document


def extract_text(filename: str, content: bytes) -> str:
    """Extract text from PDF, DOCX, or TXT content."""
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        with pymupdf.open(stream=content, filetype="pdf") as pdf:
            pages = []

            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()
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

    if not result.strip():
        raise ValueError(
            "No text was extracted. The file may be empty or scanned."
        )

    return result
