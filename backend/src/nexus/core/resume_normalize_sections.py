import json
from nexus.core.schemas.resume import ResumeData
from nexus.core.resume_normalize_common import detail_strings, first_value

def normalize_custom_sections(normalized: dict, known_aliases: set[str]) -> None:
    sections = normalized.get("additional_sections")
    if isinstance(sections, str): sections = [{"title": "Additional information", "details": sections}]
    elif isinstance(sections, dict):
        if any(key in sections for key in ("title", "section_name", "name", "heading")): sections = [sections]
        else: sections = [{"title": key.replace("_", " ").title(), "details": value} for key, value in sections.items()]
    elif not isinstance(sections, list): sections = []
    converted = []
    for section in sections:
        if isinstance(section, str):
            converted.append({"title": "Additional information", "details": detail_strings(section)})
        elif isinstance(section, dict):
            item = dict(section)
            item["title"] = str(first_value(section, "title", "section_name", "name", "heading") or "Additional information")
            item["details"] = detail_strings(first_value(section, "details", "content", "items", "bullets", "description"))
            for alias in ("section_name", "heading", "content", "items", "bullets", "description"): item.pop(alias, None)
            converted.append(item)
        else: converted.append({"title": "Additional information", "details": detail_strings(section)})
    normalized["additional_sections"] = converted

def normalize_string_collections(normalized: dict) -> None:
    fields = ("certifications", "languages", "skills", "websites", "awards", "interests", "references")
    for field in fields:
        values = normalized.get(field)
        if not isinstance(values, list): continue
        normalized[field] = [" | ".join(f"{key.replace('_', ' ').title()}: {value}" for key, value in entry.items() if value not in (None, "", [], {})) if isinstance(entry, dict) else entry for entry in values]

def retain_unknown_fields(normalized: dict, known_aliases: set[str]) -> None:
    fields = set(ResumeData.model_fields)
    custom = list(normalized.get("additional_sections") or [])
    for key in list(normalized):
        if key not in fields and key not in known_aliases:
            value = normalized.pop(key)
            if value not in (None, "", [], {}):
                values = value if isinstance(value, list) else [value]
                custom.append({"title": key.replace("_", " ").title(), "details": [item if isinstance(item, str) else json.dumps(item, ensure_ascii=False) for item in values]})
    normalized["additional_sections"] = custom
