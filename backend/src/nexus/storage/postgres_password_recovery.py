import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def store_password_reset_code(app_id: str, code_hash: str, expires_at: datetime, connect) -> None:
    """Create/replace the pending one-time recovery code for one account."""
    logger.info("Storing password recovery challenge")
    with connect() as connection:
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
                             now: datetime, token_expires_at: datetime, connect) -> bool:
    """Validate one OTP and exchange it for a single-use reset token."""
    logger.info("Validating password recovery code")
    with connect() as connection:
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
                                      password_hash: str, now: datetime, connect) -> bool:
    """Atomically replace the password and consume its validated reset token."""
    logger.info("Updating account password after verified recovery")
    with connect() as connection:
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

