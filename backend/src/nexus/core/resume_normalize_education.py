import re
from html import escape
from nexus.core.resume_normalize_common import detail_strings, normalize_items

def normalize_education(normalized: dict) -> None:
    items = normalized.get("education")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict): continue
            grade = item.get("honors_or_awards")
            if grade not in (None, "", [], {}):
                text = " ".join(detail_strings(grade))
                target = "cgpa_or_percentage" if re.search(r"\b(?:CGPA|GPA|grade|percentage|score)\b", text, re.I) else "honors"
                if item.get(target) in (None, "", [], {}): item[target] = text if target == "cgpa_or_percentage" else detail_strings(grade)
                item.pop("honors_or_awards", None)
    normalized["education"] = normalize_items(items, {
        "degree": ("degree_name", "qualification", "program"),
        "field_of_study": ("major", "field", "specialization"),
        "institution": ("university", "college", "school"),
        "location": ("location_string", "location_text", "city"),
        "start_date": ("from", "start", "startDate", "start_date_string"),
        "end_date": ("to", "end", "endDate", "end_date_string"),
        "graduation_year": ("year", "completion_year"),
        "cgpa_or_percentage": ("cgpa", "gpa", "grade", "percentage", "score"),
        "honors": ("honors_and_awards", "awards_and_honors"),
    })

def normalize_experience(normalized: dict) -> None:
    items = normalize_items(normalized.get("experience"), {
        "company": ("company_name", "employer", "organization"),
        "job_title": ("title", "position", "role", "position_title"),
        "start_date": ("from", "start", "startDate", "start_date_string"),
        "end_date": ("to", "end", "endDate", "end_date_string"),
        "responsibilities": ("duties", "key_responsibilities", "job_description", "responsibilities_and_results", "responsibilities_and_achievements"),
        "location": ("location_string", "location_text", "work_location"),
        "achievements": ("key_achievements", "results", "accomplishments"),
        "technologies": ("tools", "tech_stack"),
    })
    for item in items:
        if not isinstance(item, dict): continue
        bullets = list(dict.fromkeys([*detail_strings(item.get("responsibilities")), *detail_strings(item.get("achievements"))]))
        if bullets:
            html = "<ul>" + "".join(f"<li>{escape(bullet)}</li>" for bullet in bullets) + "</ul>"
            item["description"] = f"{item['description']}<p></p>{html}" if item.get("description") else html
            item["responsibilities"] = []; item["achievements"] = []
    normalized["experience"] = items
