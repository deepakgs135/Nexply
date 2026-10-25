"""Small, parameterized PostgreSQL access layer for user identity."""

import logging

import psycopg
from psycopg.rows import dict_row

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
