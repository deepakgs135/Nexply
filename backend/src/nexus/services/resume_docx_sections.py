from docx import Document
from nexus.services.resume_docx_components import _bullet, _extras, _line, _section, _text


def render_summary(document: Document, data: dict) -> None:
    if data.get("professional_summary"):
        _section(document, "Professional Summary")
        _line(document, _text(data["professional_summary"]))


def render_experience(document: Document, items: list[dict]) -> None:
    if not items: return
    _section(document, "Professional Experience")
    for item in items:
        role = "  |  ".join(value for value in (_text(item.get("job_title")), _text(item.get("company"))) if value)
        _line(document, role, bold_prefix=_text(item.get("job_title")))
        dates = " – ".join(value for value in (_text(item.get("start_date")), _text(item.get("end_date"))) if value)
        meta = "  |  ".join(value for value in (_text(item.get("location")), _text(item.get("employment_type")), dates) if value)
        _line(document, meta)
        _line(document, _text(item.get("description")))
        for field in ("responsibilities", "achievements"):
            for detail in item.get(field, []): _bullet(document, _text(detail))
        if item.get("technologies"): _line(document, "Technologies: " + _text(item["technologies"]))
        _extras(document, item, {"company", "job_title", "location", "employment_type", "start_date", "end_date", "description", "responsibilities", "achievements", "technologies"})


def render_skills(document: Document, data: dict) -> None:
    if data.get("skills"):
        _section(document, "Skills")
        _line(document, _text(data["skills"]))


def render_education(document: Document, items: list[dict]) -> None:
    if not items: return
    _section(document, "Education")
    for item in items:
        parts = (_text(item.get("degree")), _text(item.get("field_of_study")), _text(item.get("institution")))
        _line(document, "  |  ".join(value for value in parts if value), bold_prefix=_text(item.get("degree")))
        dates = " – ".join(value for value in (_text(item.get("start_date")), _text(item.get("end_date"))) if value)
        meta = "  |  ".join(value for value in (_text(item.get("location")), dates, _text(item.get("cgpa_or_percentage"))) if value)
        _line(document, meta)
        for field in ("coursework", "honors"):
            if item.get(field): _line(document, f"{field.replace('_', ' ').title()}: {_text(item[field])}")
        if item.get("graduation_year") is not None: _line(document, f"Graduation year: {item['graduation_year']}")
        _extras(document, item, {"degree", "field_of_study", "institution", "location", "start_date", "end_date", "graduation_year", "cgpa_or_percentage", "coursework", "honors"})
