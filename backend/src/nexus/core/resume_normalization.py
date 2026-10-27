from nexus.core.resume_normalize_education import normalize_education, normalize_experience
from nexus.core.resume_normalize_projects import normalize_projects, normalize_publications, normalize_volunteering
from nexus.core.resume_normalize_root import normalize_root_fields
from nexus.core.resume_normalize_sections import normalize_custom_sections, normalize_string_collections, retain_unknown_fields

def normalize_resume_payload(data: dict) -> dict:
    """Canonicalize legacy model keys and retain unknown facts as custom sections."""
    normalized, aliases = normalize_root_fields(data)
    normalize_education(normalized)
    normalize_experience(normalized)
    normalize_projects(normalized)
    normalize_publications(normalized)
    normalize_volunteering(normalized)
    normalize_custom_sections(normalized, aliases)
    normalize_string_collections(normalized)
    retain_unknown_fields(normalized, aliases)
    return normalized
