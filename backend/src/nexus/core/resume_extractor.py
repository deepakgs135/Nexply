"""Public compatibility facade for resume extraction and source recovery."""

import requests
from nexus.core.resume_normalization import normalize_resume_payload
from nexus.core.resume_source_contact import fill_contact_from_source
from nexus.core.resume_source_links import fill_profile_links_from_source
from nexus.core.resume_source_experience import fill_experience_dates_from_source, fill_experience_locations_from_source
from nexus.core.resume_extraction_ollama import extract_resume_data

__all__ = ["normalize_resume_payload", "fill_contact_from_source", "fill_profile_links_from_source", "fill_experience_dates_from_source", "fill_experience_locations_from_source", "extract_resume_data"]
