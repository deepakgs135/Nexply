import json
from nexus.core.resume_normalize_common import first_value

ROOT_ALIASES = {
    "professional_title": ("title", "current_title", "headline"),
    "professional_summary": ("professional_summary_text", "summary", "profile_summary", "objective"),
    "skills": ("skills_list", "technical_skills", "key_skills"),
    "education": ("education_list", "academic_history", "qualifications"),
    "experience": ("experience_list", "work_experience", "employment_history", "job_history"),
    "projects": ("projects_list", "key_projects"),
    "certifications": ("certifications_list", "licenses", "licenses_and_certifications"),
    "languages": ("languages_list",), "websites": ("links", "profile_links", "social_links"),
    "awards": ("awards_list", "honors"), "publications": ("publications_list",),
    "volunteer_experience": ("volunteering", "volunteer_work"), "interests": ("interests_list",),
    "references": ("references_list",), "additional_sections": ("additional_sections_list", "other_sections"),
}

def normalize_root_fields(data: dict) -> tuple[dict, set[str]]:
    normalized = dict(data)
    name = data.get("name")
    if isinstance(name, dict):
        parts = (name.get("first_name"), name.get("middle_name"), name.get("last_name"))
        full_name = " ".join(str(part).strip() for part in parts if part and str(part).strip())
        normalized["full_name"] = first_value(data, "full_name") or full_name or None
    elif isinstance(name, str): normalized["full_name"] = first_value(data, "full_name") or name
    normalized.pop("name", None)
    contact = data.get("contact_info") or data.get("contact_details")
    if isinstance(contact, dict):
        for field, aliases in {"email": ("email", "email_address"), "phone": ("phone", "phone_number", "mobile"), "location": ("location", "address", "city")}.items():
            normalized[field] = first_value(data, field) or first_value(contact, *aliases)
    normalized.pop("contact_info", None); normalized.pop("contact_details", None)
    aliases = {alias for values in ROOT_ALIASES.values() for alias in values}
    for field, keys in ROOT_ALIASES.items():
        source = first_value(data, *keys)
        if normalized.get(field) in (None, "", [], {}) and source is not None: normalized[field] = source
        for alias in keys: normalized.pop(alias, None)
    links = normalized.get("websites")
    if isinstance(links, str): normalized["websites"] = [links]
    elif isinstance(links, dict):
        normalized["websites"] = [f"{key.replace('_', ' ').title()}: {value}" if isinstance(value, str) else json.dumps({key: value}, ensure_ascii=False) for key, value in links.items()]
    return normalized, aliases
