from docx import Document
from nexus.services.resume_docx_components import _bullet, _extras, _line, _section, _text


def render_projects(document: Document, items: list[dict]) -> None:
    if not items: return
    _section(document, "Projects")
    for item in items:
        title = "  |  ".join(value for value in (_text(item.get("name")), _text(item.get("role"))) if value)
        _line(document, title, bold_prefix=_text(item.get("name")))
        _line(document, _text(item.get("description")))
        for field in ("responsibilities", "outcomes"):
            for detail in item.get(field, []): _bullet(document, _text(detail))
        if item.get("technologies"): _line(document, "Technologies: " + _text(item["technologies"]))
        dates = " – ".join(value for value in (_text(item.get("start_date")), _text(item.get("end_date"))) if value)
        _line(document, "  |  ".join(value for value in (_text(item.get("url")), dates) if value))
        _extras(document, item, {"name", "role", "description", "start_date", "end_date", "url", "technologies", "responsibilities", "outcomes"})


def render_custom_sections(document: Document, items: list[dict]) -> None:
    for item in items:
        _section(document, _text(item.get("title")) or "Additional Information")
        for detail in item.get("details", []): _bullet(document, _text(detail))
        _extras(document, item, {"title", "details"})
