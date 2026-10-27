from docx import Document
from nexus.services.resume_docx_components import _bullet, _extras, _line, _section, _text


def render_additional(document: Document, data: dict) -> None:
    sections = (("Certifications", "certifications"), ("Languages", "languages"), ("Awards", "awards"),
                ("Volunteer Experience", "volunteer_experience"), ("Publications", "publications"),
                ("Interests", "interests"), ("References", "references"))
    for title, key in sections:
        items = data.get(key) or []
        if not items: continue
        _section(document, title)
        if key in {"volunteer_experience", "publications"}:
            for item in items:
                role = item.get("job_title") or item.get("title")
                org = item.get("company") or item.get("publisher")
                _line(document, " | ".join(value for value in (_text(role), _text(org)) if value), bold_prefix=_text(role))
                details = (item.get("description"), item.get("publication_date"), item.get("url"))
                _line(document, " | ".join(value for value in map(_text, details) if value))
                for detail in item.get("responsibilities", []): _bullet(document, _text(detail))
                _extras(document, item, {"company", "job_title", "location", "employment_type", "start_date", "end_date", "description", "responsibilities", "achievements", "technologies", "title", "publisher", "publication_date", "url"})
        else:
            for item in items: _bullet(document, _text(item))
