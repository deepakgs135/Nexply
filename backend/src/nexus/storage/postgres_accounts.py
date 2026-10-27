import logging

logger = logging.getLogger(__name__)

def create_user(full_name: str, email: str, password_hash: str, connect) -> dict:
    """Insert a user; PostgreSQL generates both id and app_id."""
    logger.info("Creating account email_hash_scope=normalized")
    with connect() as connection:
        row = connection.execute(
            """INSERT INTO public.users (full_name, email, password_hash, app_id)
               VALUES (%s, %s, %s, gen_random_uuid())
               RETURNING id, app_id, full_name, email, is_active, created_at""",
            (full_name, email, password_hash),
        ).fetchone()
    return dict(row)
def get_user_by_email(email: str, connect) -> dict | None:
    logger.info("Looking up account by normalized email")
    with connect() as connection:
        row = connection.execute(
            """SELECT id, app_id, full_name, email, password_hash, is_active, created_at
               FROM public.users WHERE email = %s""",
            (email,),
        ).fetchone()
    return dict(row) if row else None
def get_user_by_app_id(app_id: str, connect) -> dict | None:
    logger.info("Resolving authenticated account from PostgreSQL")
    with connect() as connection:
        row = connection.execute(
            """SELECT id, app_id, full_name, email, is_active, created_at
               FROM public.users WHERE app_id = %s::uuid""",
            (app_id,),
        ).fetchone()
    return dict(row) if row else None

