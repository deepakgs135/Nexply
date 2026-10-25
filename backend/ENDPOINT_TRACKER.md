# NEXPLY API endpoint tracker

Last reviewed: 2026-10-25

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
| `POST /resumes/upload` | Yes | Yes | Requires bearer authentication and a UUID `Idempotency-Key`. Retries for the same user/key/file reuse the same MongoDB record; concurrent duplicate GridFS uploads are cleaned up. |
| `GET /resumes/{document_id}` | Yes | Yes | Requires bearer authentication and scopes lookup by document id plus PostgreSQL-derived `app_id`; legacy records without ownership are inaccessible. |
| `GET /resumes/history` | Yes | Yes | Authenticated, paginated resume list; MongoDB query and count both filter by the current user's `app_id`. Returns lightweight summaries, not parsed source text. |
| `GET /resumes/{document_id}/profile` | Yes | Yes | Authenticated owner-scoped profile detail for the selected history item; returns structured data only and does not return parsed text or GridFS identifiers. |
| `PUT /resumes/{document_id}/structured-result` | Yes | Yes | Validates edited structured data and updates the existing resume record using the authenticated user's `app_id`; does not insert a new document. |
| `DELETE /resumes/{document_id}` | Yes | Yes | Owner-scoped hard delete removes the resume record plus its original GridFS file and other GridFS originals associated with the resume. |
| `GET /resumes/ai/models` | Yes | Yes | Lists locally installed Ollama text-generation models for the optional AI Smart resume writer. |
| `POST /resumes/{document_id}/ai-resume` | Yes | Yes | Generates a non-persisted profile draft from the owner's saved structured profile, with an optional target job description. |
| `POST /resumes/{document_id}/ai-resume/export` | Yes | Yes | Owner-checked DOCX download generated in memory; does not create a resume or GridFS record. |
| `POST /resumes/{document_id}/parse` | Yes | Yes | Requires bearer authentication; document reads and parsed-text/status updates are owner-filtered. |
| `POST /resumes/{document_id}/extract` | Yes | Yes | Requires bearer authentication; document reads and structured-result/status updates are owner-filtered. |
| Job description upload/create endpoint | No | No | `jd` repository/service helpers exist, but there is no upload/create route wired into `main.py`. |
| Job description parse endpoint | No | No | `save_parsed_jd()` exists, but no file-backed parse flow or route is wired in. |
| Job description get endpoint | No | No | Repository lookup helper exists, but no route is wired in. |

## Database state checked

- The application is already configured to use `nexply` by default (`MONGODB_DATABASE`, overrideable through the environment).
- `nexply` currently has the `resume` application collection with 4 records; `jd` has not been materialized yet. GridFS uses the supporting `document_files.files` and `document_files.chunks` collections. The fictional end-to-end fixture was stored only in `nexply_human_test`, which was dropped after testing; no fixture record remains in `nexply`.
- The existing `nexus_ai.documents` record and its original GridFS file are still present. No migration or deletion was performed.
- The `nexply` resume record `6adda9b650f84544a4aabea5` has parsed text and now has a structured result; `llm_status=completed` and `llm_error` is cleared.

## API test run

- Swagger UI and `/openapi.json` both returned HTTP 200; OpenAPI lists health, auth, and protected resume routes.
- `python -m pytest -q`: 69 passed, 1 existing Starlette deprecation warning. Authentication tests use an isolated mocked PostgreSQL repository; no user was created and no schema or database records were changed.
- MongoDB owner-filter tests verify resume and JD lookups/updates include both `_id` and `app_id`, create helpers override client-supplied owners with the authenticated owner, and updates cannot change `_id` or `app_id`. Upload tests cover owner metadata and idempotent retries.
- This checkout's `.env` does not yet define `DATABASE_URL` or `JWT_SECRET_KEY`; a read-only connection attempt as `nexply_app` also confirmed PostgreSQL requires a password. Run a live sign-up/sign-in check after configuring those local values.
- A human-style flow used the fictional fixture at `tests/fixtures/mock_resume.txt` against an isolated API instance and temporary `nexply_human_test` database: upload 201, parse 200 (628 characters), extract 200, and get 200. The original was found in GridFS; parsed text and structured JSON were inline; the response hid the GridFS ID.
- Human checks matched the sample's name, email, skill, education, employer, and project. The temporary database was dropped and the isolated server was stopped after the run.
- The existing resume's Ollama extraction was also exercised separately through the API and completed successfully after the thinking/schema fix.

## Storage target

Keep application records in `nexply.resume` and `nexply.jd`, with complete `parsed_text` and validated `structured_result` stored inline. Keep only uploaded originals in the `document_files` GridFS bucket. Preserve `nexus_ai` during the transition.
