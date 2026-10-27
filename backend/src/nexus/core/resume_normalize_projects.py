from nexus.core.resume_normalize_common import normalize_items

def normalize_projects(normalized: dict) -> None:
    normalized["projects"] = normalize_items(normalized.get("projects"), {
        "name": ("project_name", "title"), "description": ("overview", "summary"),
        "technologies": ("tools", "tech_stack", "technology_stack"),
        "responsibilities": ("contributions", "key_contributions"),
        "outcomes": ("results", "achievements"),
    })

def normalize_publications(normalized: dict) -> None:
    normalized["publications"] = normalize_items(normalized.get("publications"), {
        "title": ("name", "paper_title"), "publisher": ("journal", "organization", "venue"),
        "publication_date": ("date", "published_at"), "url": ("link",),
    })

def normalize_volunteering(normalized: dict) -> None:
    normalized["volunteer_experience"] = normalize_items(normalized.get("volunteer_experience"), {
        "company": ("organization", "company_name"), "job_title": ("title", "role", "position"),
        "start_date": ("from", "start"), "end_date": ("to", "end"),
        "responsibilities": ("duties", "contributions"),
    })
