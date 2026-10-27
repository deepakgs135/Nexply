"""Small, parameterized PostgreSQL access layer for user identity."""

import logging
from datetime import datetime

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from nexus.core.config import DATABASE_URL

logger = logging.getLogger(__name__)


def _connect():
    if not DATABASE_URL:
        raise RuntimeError("PostgreSQL DATABASE_URL is not configured.")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def create_user(full_name: str, email: str, password_hash: str) -> dict:
    """Insert a user; PostgreSQL generates both id and app_id."""
    logger.info("Creating account email_hash_scope=normalized")
    with _connect() as connection:
        row = connection.execute(
            """INSERT INTO public.users (full_name, email, password_hash, app_id)
               VALUES (%s, %s, %s, gen_random_uuid())
               RETURNING id, app_id, full_name, email, is_active, created_at""",
            (full_name, email, password_hash),
        ).fetchone()
    return dict(row)


def get_user_by_email(email: str) -> dict | None:
    logger.info("Looking up account by normalized email")
    with _connect() as connection:
        row = connection.execute(
            """SELECT id, app_id, full_name, email, password_hash, is_active, created_at
               FROM public.users WHERE email = %s""",
            (email,),
        ).fetchone()
    return dict(row) if row else None


def get_user_by_app_id(app_id: str) -> dict | None:
    logger.info("Resolving authenticated account from PostgreSQL")
    with _connect() as connection:
        row = connection.execute(
            """SELECT id, app_id, full_name, email, is_active, created_at
               FROM public.users WHERE app_id = %s::uuid""",
            (app_id,),
        ).fetchone()
    return dict(row) if row else None


def get_job_preferences(app_id: str) -> dict | None:
    """Load job preferences by the authenticated user's unique app_id."""
    logger.info("Loading job preferences for authenticated account")
    with _connect() as connection:
        row = connection.execute(
            """SELECT current_ctc, expected_ctc, expected_ctc_range,
                      minimum_expected_ctc, currency, preferred_locations,
                      preferred_job_titles, work_mode, employment_types,
                      notice_period, availability, willing_to_relocate,
                      preferred_industries
               FROM public.user_job_preferences WHERE app_id = %s::uuid""",
            (app_id,),
        ).fetchone()
    return dict(row) if row else None


def upsert_job_preferences(app_id: str, preferences: dict) -> dict:
    """Insert or replace preferences without accepting app_id from the client."""
    logger.info("Saving job preferences for authenticated account")
    values = (
        preferences.get("current_ctc"), preferences.get("expected_ctc"),
        preferences.get("expected_ctc_range"), preferences.get("minimum_expected_ctc"),
        preferences.get("currency") or "INR", Jsonb(preferences.get("preferred_locations") or []),
        Jsonb(preferences.get("preferred_job_titles") or []), preferences.get("work_mode"),
        Jsonb(preferences.get("employment_types") or []), preferences.get("notice_period"),
        preferences.get("availability"), preferences.get("willing_to_relocate"),
        Jsonb(preferences.get("preferred_industries") or []), app_id,
    )
    with _connect() as connection:
        row = connection.execute(
            """INSERT INTO public.user_job_preferences
                 (current_ctc, expected_ctc, expected_ctc_range, minimum_expected_ctc,
                  currency, preferred_locations, preferred_job_titles, work_mode,
                  employment_types, notice_period, availability, willing_to_relocate,
                  preferred_industries, app_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::uuid)
               ON CONFLICT (app_id) DO UPDATE SET
                 current_ctc = EXCLUDED.current_ctc,
                 expected_ctc = EXCLUDED.expected_ctc,
                 expected_ctc_range = EXCLUDED.expected_ctc_range,
                 minimum_expected_ctc = EXCLUDED.minimum_expected_ctc,
                 currency = EXCLUDED.currency,
                 preferred_locations = EXCLUDED.preferred_locations,
                 preferred_job_titles = EXCLUDED.preferred_job_titles,
                 work_mode = EXCLUDED.work_mode,
                 employment_types = EXCLUDED.employment_types,
                 notice_period = EXCLUDED.notice_period,
                 availability = EXCLUDED.availability,
                 willing_to_relocate = EXCLUDED.willing_to_relocate,
                 preferred_industries = EXCLUDED.preferred_industries,
                 updated_at = NOW()
               RETURNING app_id""",
            values,
        ).fetchone()
    return {"app_id": str(row["app_id"])}


def upsert_candidate_profile(
    app_id: str,
    source_document_id: str,
    original_filename: str | None,
    profile: dict,
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
    with _connect() as connection:
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


def get_candidate_profile_source_document_id(app_id: str) -> str | None:
    """Return the Mongo source id currently mirrored for this account."""
    with _connect() as connection:
        row = connection.execute(
            "SELECT source_document_id FROM public.candidate_profiles WHERE app_id = %s::uuid",
            (app_id,),
        ).fetchone()
    return row["source_document_id"] if row else None


def store_password_reset_code(app_id: str, code_hash: str, expires_at: datetime) -> None:
    """Create/replace the pending one-time recovery code for one account."""
    logger.info("Storing password recovery challenge")
    with _connect() as connection:
        connection.execute(
            """INSERT INTO public.password_reset_challenges
                   (app_id, code_hash, code_expires_at, attempts, reset_token_hash,
                    reset_token_expires_at, updated_at)
               VALUES (%s::uuid, %s, %s, 0, NULL, NULL, NOW())
               ON CONFLICT (app_id) DO UPDATE SET
                   code_hash = EXCLUDED.code_hash,
                   code_expires_at = EXCLUDED.code_expires_at,
                   attempts = 0,
                   reset_token_hash = NULL,
                   reset_token_expires_at = NULL,
                   updated_at = NOW()""",
            (app_id, code_hash, expires_at),
        )


def set_reset_token_for_code(email: str, code_hash: str, token_hash: str,
                             now: datetime, token_expires_at: datetime) -> bool:
    """Validate one OTP and exchange it for a single-use reset token."""
    logger.info("Validating password recovery code")
    with _connect() as connection:
        connection.execute(
            """UPDATE public.password_reset_challenges AS challenge
               SET attempts = attempts + 1, updated_at = NOW()
               FROM public.users AS account
               WHERE challenge.app_id = account.app_id AND account.email = %s
                 AND challenge.code_expires_at > %s AND challenge.attempts < 5
                 AND challenge.code_hash <> %s
                 AND challenge.reset_token_hash IS NULL""",
            (email, now, code_hash),
        )
        row = connection.execute(
            """UPDATE public.password_reset_challenges AS challenge
               SET reset_token_hash = %s, reset_token_expires_at = %s, updated_at = NOW()
               FROM public.users AS account
               WHERE challenge.app_id = account.app_id AND account.email = %s
                 AND challenge.code_hash = %s AND challenge.code_expires_at > %s
                 AND challenge.attempts < 5 AND challenge.reset_token_hash IS NULL
               RETURNING challenge.app_id""",
            (token_hash, token_expires_at, email, code_hash, now),
        ).fetchone()
    return row is not None


def replace_password_with_reset_token(email: str, token_hash: str,
                                      password_hash: str, now: datetime) -> bool:
    """Atomically replace the password and consume its validated reset token."""
    logger.info("Updating account password after verified recovery")
    with _connect() as connection:
        row = connection.execute(
            """SELECT account.app_id FROM public.users AS account
               JOIN public.password_reset_challenges AS challenge
                 ON challenge.app_id = account.app_id
               WHERE account.email = %s AND account.is_active = TRUE
                 AND challenge.reset_token_hash = %s
                 AND challenge.reset_token_expires_at > %s
               FOR UPDATE OF account, challenge""",
            (email, token_hash, now),
        ).fetchone()
        if not row:
            return False
        connection.execute(
            "UPDATE public.users SET password_hash = %s WHERE app_id = %s",
            (password_hash, row["app_id"]),
        )
        connection.execute(
            "DELETE FROM public.password_reset_challenges WHERE app_id = %s",
            (row["app_id"],),
        )
    return True
