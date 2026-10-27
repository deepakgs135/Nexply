# NEXPLY API endpoint tracker

Last reviewed: 2026-10-27

`Implemented` describes whether the route exists in the current application. `Tested` records a live or automated check; the result notes whether persistence or model calls were mocked.

| Endpoint | Implemented | Tested | Current result / next step |
|---|---|---|---|
| `GET /` | Yes | Yes | Serves the built React + TypeScript workspace from `frontend/dist`; in Vite development mode use port 5173. |
| `GET /api/config` | Yes | Yes | Returns configured upload size and supported formats for UI validation. |
| `GET /assets/*` | Yes | Yes | Serves Vite-built React bundles and styles. |
| `GET /health` | Yes | Yes | 200; local MongoDB ping succeeds and reports `nexply`. |
| `POST /auth/register` | Yes | Yes | Isolated automated tests cover normalization, Argon2id hashing, database-generated `app_id`, token response, and duplicate rejection. PostgreSQL integration remains pending local `DATABASE_URL` setup. |
| `POST /auth/login` | Yes | Yes | Isolated automated tests cover correct/incorrect credentials, inactive accounts, and generic credential errors. |
| `GET /auth/me` | Yes | Yes | Tests cover valid, missing, malformed, expired, and forged tokens; PostgreSQL account lookup; and secret-free profile output. |
| `POST /auth/password-reset/request` | Yes | No | Implemented with SMTP-delivered six-digit OTP, expiring hashed challenge, and generic account-existence response. Configure SMTP values in `.env` before using. |
| `POST /auth/password-reset/verify` | Yes | No | Implemented with OTP expiration and five-attempt limit; successful verification returns a short-lived single-use reset token. |
| `POST /auth/password-reset/complete` | Yes | No | Implemented with password confirmation, Argon2id rehash, and atomic one-time token consumption. |
| `POST /resumes/upload` | Yes | Yes | Requires bearer authentication and a UUID `Idempotency-Key`. Retries for the same user/key/file reuse the same MongoDB record; concurrent duplicate GridFS uploads are cleaned up. |
| `GET /resumes/{document_id}` | Yes | Yes | Requires bearer authentication and scopes lookup by document id plus PostgreSQL-derived `app_id`; legacy records without ownership are inaccessible. |
| `GET /resumes/latest` | Yes | Yes | Returns the current profile and backfills its structured result to `public.candidate_profiles` when the authenticated user's SQL row is missing, stale, or marked unsynchronized. |
| `GET /resumes/{document_id}/profile` | Yes | Yes | Authenticated owner-scoped profile detail; returns structured data only and does not return parsed text or GridFS identifiers. |
| `PUT /resumes/{document_id}/structured-result` | Yes | Yes | Validates and saves edits to the existing MongoDB record, then upserts the same user's SQL row by `app_id`. |
| `GET /resumes/preferences` | Yes | Yes | Loads preferences from `public.user_job_preferences` using the authenticated PostgreSQL `app_id`; returns empty defaults with `configured: false` if the manual table is not installed. |
| `PUT /resumes/preferences` | Yes | Yes | Upserts preferences into PostgreSQL using the authenticated `app_id`; client-supplied account identifiers are ignored. |
| `DELETE /resumes/{document_id}` | Yes | Yes | Owner-scoped hard delete removes the resume record plus its original GridFS file and other GridFS originals associated with the resume. |
| `GET /resumes/ai/models` | Yes | Yes | Lists locally installed Ollama text-generation models for the optional AI Smart resume writer. |
| `POST /resumes/{document_id}/ai-resume` | Yes | Yes | Generates a non-persisted profile draft from the owner's saved structured profile, with an optional target job description. |
| `POST /resumes/{document_id}/rex/rewrite` | Yes | Yes | Rewrites or drafts the requested summary/description from owner-scoped profile facts in 2, 5, or 8 lines (concise, brief, or detail); applies to the unsaved editor draft and persists only after user Save. |
| `POST /resumes/manual-profile/interview` | Yes | Yes | Authenticated REX interview extracts only user-provided facts and asks one dynamic follow-up; route behavior is mocked in tests, live Ollama interview not yet tested. |
| `POST /resumes/manual-profile` | Yes | Yes | Saves the manual profile to MongoDB, removes older owner records, then upserts the same user's SQL row by `app_id`. |
| `POST /resumes/{document_id}/ai-resume/export` | Yes | Yes | Owner-checked DOCX download generated in memory; does not create a resume or GridFS record. |
| `POST /resumes/{document_id}/parse` | Yes | Yes | Requires bearer authentication; document reads and parsed-text/status updates are owner-filtered. |
| `POST /resumes/{document_id}/extract` | Yes | Yes | Requires bearer authentication; saves extracted JSON to the owner-scoped MongoDB record, then upserts the same SQL row by `app_id`. PostgreSQL failures are reported as sync errors and retryable on the next save/profile load. |
| Job description upload/create endpoint | No | No | `jd` repository/service helpers exist, but there is no upload/create route wired into `main.py`. |
| Job description parse endpoint | No | No | `save_parsed_jd()` exists, but no file-backed parse flow or route is wired in. |
| Job description get endpoint | No | No | Repository lookup helper exists, but no route is wired in. |

## Database state checked

- The application is already configured to use `nexply` by default (`MONGODB_DATABASE`, overrideable through the environment).
- The Profile workspace now calls `/resumes/latest`; it retains the newest resume for the signed-in owner and removes older owner records and associated GridFS originals. Uploads and manual saves apply the same latest-only retention.
- The existing `nexus_ai.documents` record and its original GridFS file remain untouched.
- PostgreSQL password recovery uses the additive `password_reset_challenges` table. Its migration was applied locally; the existing `public.users` table was not altered.
- Structured resume data is mirrored to `public.candidate_profiles`, whose `app_id` primary key enforces one row per user. Extraction, manual profile creation, edits, and profile loading all use an `ON CONFLICT (app_id) DO UPDATE` upsert. The configured `nexply_app` role has SELECT/INSERT/UPDATE privileges on this table.
- The current structured MongoDB profile was backfilled to `public.candidate_profiles`; the stored source document id matches MongoDB, and a row-count check confirmed exactly one row for that `app_id`.

## API test run

- Swagger UI and `/openapi.json` both returned HTTP 200; OpenAPI lists health, auth, and protected resume routes.
- `python -m pytest -q`: 94 passed, 1 existing Starlette deprecation warning. Authentication tests use a mocked PostgreSQL repository.
- MongoDB owner-filter tests verify resume and JD lookups/updates include both `_id` and `app_id`, create helpers override client-supplied owners with the authenticated owner, and updates cannot change `_id` or `app_id`. Upload tests cover owner metadata and idempotent retries.
- The built React/TypeScript workspace compiles with `npm run build`; Python source compilation also succeeds.
- A human-style flow used the fictional fixture at `tests/fixtures/mock_resume.txt` against an isolated API instance and temporary `nexply_human_test` database: upload 201, parse 200 (628 characters), extract 200, and get 200. The original was found in GridFS; parsed text and structured JSON were inline; the response hid the GridFS ID.
- Human checks matched the sample's name, email, skill, education, employer, and project. The temporary database was dropped and the isolated server was stopped after the run.
- The existing resume's Ollama extraction was also exercised separately through the API and completed successfully after the thinking/schema fix.
- Experience normalization was checked against the current MongoDB profile: all seven source bullets are restored into responsibilities, and `location_string` / separate source location lines map into the location field. This compatibility check read the record without modifying it.
- The Profile UI no longer shows a structured-output panel; it shows editable job preferences, with the structured resume loaded into the right-side blocks. Preferences are stored in PostgreSQL; run `docs/sql/user_job_preferences.sql` manually to create the table.
- Experience bullets normalize into a rich-text unordered list in the Description field, and malformed model aliases are removed. Location aliases and locations from the parsed source are normalized into the canonical location field.

## Storage target

Keep application records in `nexply.resume` and `nexply.jd`, with complete `parsed_text` and validated `structured_result` stored inline. Keep only uploaded originals in the `document_files` GridFS bucket. Preserve `nexus_ai` during the transition.
