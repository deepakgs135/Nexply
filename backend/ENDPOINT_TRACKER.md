# NEXPLY API endpoint tracker

Last reviewed: 2026-10-25

`Implemented` describes whether the route exists in the current application. `Tested` records a live or automated check; the result notes whether persistence or model calls were mocked.

| Endpoint | Implemented | Tested | Current result / next step |
|---|---|---|---|
| `GET /` | Yes | Yes | Serves the built React + TypeScript workspace from `frontend/dist`; in Vite development mode use port 5173. |
| `GET /api/config` | Yes | Yes | Returns configured upload size and supported formats for UI validation. |
| `GET /assets/*` | Yes | Yes | Serves Vite-built React bundles and styles. |
| `GET /health` | Yes | Yes | 200; local MongoDB ping succeeds and reports `nexply`. |
| `POST /resumes/upload` | Yes | Yes | Automated validation tests plus live upload of the fictional TXT fixture to an isolated database returned 201. |
| `GET /resumes/{document_id}` | Yes | Yes | 200 for existing resume `6adda9b650f84544a4aabea5`; parsed text is returned with 5,215 characters. Also verified the end-to-end test record and inline parsed/structured fields. |
| `POST /resumes/{document_id}/parse` | Yes | Yes | Automated route test plus live parse of the fictional fixture returned 200 and extracted 628 characters. Direct parser check also extracted 3 pages and 5,215 characters from the existing PDF. |
| `POST /resumes/{document_id}/extract` | Yes | Yes | Automated route test plus live Ollama extraction on the fixture returned 200; expected name, email, skill, school, employer, and project matched. Existing resume extraction also completed successfully. |
| Job description upload/create endpoint | No | No | `jd` repository/service helpers exist, but there is no upload/create route wired into `main.py`. |
| Job description parse endpoint | No | No | `save_parsed_jd()` exists, but no file-backed parse flow or route is wired in. |
| Job description get endpoint | No | No | Repository lookup helper exists, but no route is wired in. |

## Database state checked

- The application is already configured to use `nexply` by default (`MONGODB_DATABASE`, overrideable through the environment).
- `nexply` currently has the `resume` application collection with 4 records; `jd` has not been materialized yet. GridFS uses the supporting `document_files.files` and `document_files.chunks` collections. The fictional end-to-end fixture was stored only in `nexply_human_test`, which was dropped after testing; no fixture record remains in `nexply`.
- The existing `nexus_ai.documents` record and its original GridFS file are still present. No migration or deletion was performed.
- The `nexply` resume record `6adda9b650f84544a4aabea5` has parsed text and now has a structured result; `llm_status=completed` and `llm_error` is cleared.

## API test run

- Swagger UI and `/openapi.json` both returned HTTP 200; OpenAPI lists the health, resume upload, parse, extract, and get routes.
- `python -m pytest -q`: 8 passed. These tests mock persistence and extraction, so they do not create MongoDB records or call Ollama.
- A human-style flow used the fictional fixture at `tests/fixtures/mock_resume.txt` against an isolated API instance and temporary `nexply_human_test` database: upload 201, parse 200 (628 characters), extract 200, and get 200. The original was found in GridFS; parsed text and structured JSON were inline; the response hid the GridFS ID.
- Human checks matched the sample's name, email, skill, education, employer, and project. The temporary database was dropped and the isolated server was stopped after the run.
- The existing resume's Ollama extraction was also exercised separately through the API and completed successfully after the thinking/schema fix.

## Storage target

Keep application records in `nexply.resume` and `nexply.jd`, with complete `parsed_text` and validated `structured_result` stored inline. Keep only uploaded originals in the `document_files` GridFS bucket. Preserve `nexus_ai` during the transition.
