import logging
from psycopg.types.json import Jsonb

logger = logging.getLogger(__name__)

def upsert_candidate_profile(
    app_id: str,
    source_document_id: str,
    original_filename: str | None,
    profile: dict,
    connect,
) -> None:
    """Mirror one MongoDB structured resume into the user's single SQL row."""
    logger.info("Upserting structured candidate profile by authenticated app_id")
    values = (
        app_id, source_document_id, original_filename,
        profile.get("full_name"), profile.get("email"), profile.get("phone"),
        profile.get("location"), profile.get("professional_title"),
        profile.get("professional_summary"),
        Jsonb(profile.get("skills") or []), Jsonb(profile.get("education") or []),
        Jsonb(profile.get("experience") or []), Jsonb(profile.get("projects") or []),
        Jsonb(profile.get("certifications") or []), Jsonb(profile.get("languages") or []),
        Jsonb(profile.get("websites") or []), Jsonb(profile.get("awards") or []),
        Jsonb(profile.get("publications") or []),
        Jsonb(profile.get("volunteer_experience") or []),
        Jsonb(profile.get("interests") or []), Jsonb(profile.get("references") or []),
        Jsonb(profile.get("additional_sections") or []),
    )
    with connect() as connection:
        connection.execute(
            """INSERT INTO public.candidate_profiles (
                   app_id, source_document_id, original_filename, full_name, email,
                   phone, location, professional_title, professional_summary,
                   skills, education, experience, projects, certifications, languages,
                   websites, awards, publications, volunteer_experience, interests,
                   references_list, additional_sections
               ) VALUES (
                   %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s,
                   %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
               )
               ON CONFLICT (app_id) DO UPDATE SET
                   source_document_id = EXCLUDED.source_document_id,
                   original_filename = EXCLUDED.original_filename,
                   full_name = EXCLUDED.full_name,
                   email = EXCLUDED.email,
                   phone = EXCLUDED.phone,
                   location = EXCLUDED.location,
                   professional_title = EXCLUDED.professional_title,
                   professional_summary = EXCLUDED.professional_summary,
                   skills = EXCLUDED.skills,
                   education = EXCLUDED.education,
                   experience = EXCLUDED.experience,
                   projects = EXCLUDED.projects,
                   certifications = EXCLUDED.certifications,
                   languages = EXCLUDED.languages,
                   websites = EXCLUDED.websites,
                   awards = EXCLUDED.awards,
                   publications = EXCLUDED.publications,
                   volunteer_experience = EXCLUDED.volunteer_experience,
                   interests = EXCLUDED.interests,
                   references_list = EXCLUDED.references_list,
                   additional_sections = EXCLUDED.additional_sections,
                   updated_at = NOW()""",
            values,
        )
def get_candidate_profile_source_document_id(app_id: str, connect) -> str | None:
    """Return the Mongo source id currently mirrored for this account."""
    with connect() as connection:
        row = connection.execute(
            "SELECT source_document_id FROM public.candidate_profiles WHERE app_id = %s::uuid",
            (app_id,),
        ).fetchone()
    return row["source_document_id"] if row else None

