"""PostgreSQL repository facade; SQL statements live in domain modules."""

import psycopg
from psycopg.rows import dict_row
from nexus.core.config import DATABASE_URL
from nexus.core.debug import debug_trace
from nexus.storage import postgres_accounts, postgres_password_recovery, postgres_preferences, postgres_profiles


def _connect():
    if not DATABASE_URL:
        raise RuntimeError("PostgreSQL DATABASE_URL is not configured.")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@debug_trace
def create_user(full_name: str, email: str, password_hash: str) -> dict:
    return postgres_accounts.create_user(full_name, email, password_hash, connect=_connect)


@debug_trace
def get_user_by_email(email: str) -> dict | None:
    return postgres_accounts.get_user_by_email(email, connect=_connect)


@debug_trace
def get_user_by_app_id(app_id: str) -> dict | None:
    return postgres_accounts.get_user_by_app_id(app_id, connect=_connect)


@debug_trace
def get_job_preferences(app_id: str) -> dict | None:
    return postgres_preferences.get_job_preferences(app_id, connect=_connect)


@debug_trace
def upsert_job_preferences(app_id: str, preferences: dict) -> dict:
    return postgres_preferences.upsert_job_preferences(app_id, preferences, connect=_connect)


@debug_trace
def upsert_candidate_profile(app_id: str, source_document_id: str, original_filename: str | None, profile: dict) -> None:
    return postgres_profiles.upsert_candidate_profile(app_id, source_document_id, original_filename, profile, connect=_connect)


@debug_trace
def get_candidate_profile_source_document_id(app_id: str) -> str | None:
    return postgres_profiles.get_candidate_profile_source_document_id(app_id, connect=_connect)


@debug_trace
def store_password_reset_code(app_id: str, code_hash: str, expires_at) -> None:
    return postgres_password_recovery.store_password_reset_code(app_id, code_hash, expires_at, connect=_connect)


@debug_trace
def set_reset_token_for_code(email: str, code_hash: str, token_hash: str, now, token_expires_at) -> bool:
    return postgres_password_recovery.set_reset_token_for_code(email, code_hash, token_hash, now, token_expires_at, connect=_connect)


@debug_trace
def replace_password_with_reset_token(email: str, token_hash: str, password_hash: str, now) -> bool:
    return postgres_password_recovery.replace_password_with_reset_token(email, token_hash, password_hash, now, connect=_connect)

@debug_trace
def get_candidate_profile(app_id: str) -> dict | None:
    return postgres_profiles.get_candidate_profile(
        app_id,
        connect=_connect,
    )