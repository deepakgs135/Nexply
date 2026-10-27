import logging
from psycopg.types.json import Jsonb

logger = logging.getLogger(__name__)

def get_job_preferences(app_id: str, connect) -> dict | None:
    """Load job preferences by the authenticated user's unique app_id."""
    logger.info("Loading job preferences for authenticated account")
    with connect() as connection:
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
def upsert_job_preferences(app_id: str, preferences: dict, connect) -> dict:
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
    with connect() as connection:
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

