
from nexus.core.debug import debug_trace
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
import re

import pymupdf
from docx import Document


@debug_trace
def _extract_profile_links(page) -> list[str]:
    """Read common profile URLs from PDF link annotations, not just visible text."""
    recognized_domains = {
        "linkedin.com": "LinkedIn",
        "github.com": "GitHub",
        "leetcode.com": "LeetCode",
        "gitlab.com": "GitLab",
        "kaggle.com": "Kaggle",
        "behance.net": "Behance",
        "dribbble.com": "Dribbble",
        "medium.com": "Medium",
    }
    links = []
    for link in page.get_links():
        uri = (link.get("uri") or "").strip()
        parsed = urlparse(uri)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            continue
        hostname = parsed.hostname.lower().removeprefix("www.")
        label = next((name for domain, name in recognized_domains.items() if hostname == domain or hostname.endswith(f".{domain}")), None)
        visible_text = ""
        rect = link.get("from")
        if rect:
            visible_text = re.sub(r"\s+", " ", page.get_textbox(rect)).strip()
        if label == "GitHub":
            path_parts = [part for part in parsed.path.split("/") if part]
            if len(path_parts) > 1 and visible_text.casefold() not in {"github", "github profile"}:
                continue
        if not label and "portfolio" in hostname:
            label = "Portfolio"
        if not label and visible_text.casefold() in {"portfolio", "personal website", "website"}:
            label = "Portfolio" if visible_text.casefold() == "portfolio" else "Website"
        if label:
            links.append(f"{label}: {uri.rstrip('.,;!')}")
    return list(dict.fromkeys(links))


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
                profile_links = _extract_profile_links(page)
                if profile_links:
                    link_text = "\n\nProfile links:\n" + "\n".join(profile_links)
                    text = f"{text}{link_text}" if text else link_text.strip()
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
