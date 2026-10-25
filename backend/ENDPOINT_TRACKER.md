# NEXPLY API endpoint tracker

Last reviewed: 2026-10-25

`Implemented` describes whether the route exists in the current application. `Tested` records a live or automated check; the result notes whether persistence or model calls were mocked.

| Endpoint | Implemented | Tested | Current result / next step |
|---|---|---|---|
| `GET /` | Yes | Yes | 200; app reports running. |
| `GET /health` | Yes | Yes | 200; local MongoDB ping succeeds and reports `nexply`. |
| `POST /resumes/upload` | Yes | Yes (automated; storage mocked) | Valid TXT upload returns 201; unsupported extension returns 415. No MongoDB record was created by these tests. |
| `GET /resumes/{document_id}` | Yes | Yes | 200 for existing resume `6adda9b650f84544a4aabea5`; parsed text is returned with 5,215 characters. |
| `POST /resumes/{document_id}/parse` | Yes | Yes (automated; service mocked) | Route returns the parsing service result; direct parser check extracted 3 pages and 5,215 characters from the PDF. |
| `POST /resumes/{document_id}/extract` | Yes | Yes | API test checks response handling with extraction mocked. Separately, live extraction on record `6adda9b650f84544a4aabea5` returned 200 and stored `llm_status=completed`. |
| Job description upload/create endpoint | No | No | `jd` repository/service helpers exist, but there is no upload/create route wired into `main.py`. |
| Job description parse endpoint | No | No | `save_parsed_jd()` exists, but no file-backed parse flow or route is wired in. |
| Job description get endpoint | No | No | Repository lookup helper exists, but no route is wired in. |

## Database state checked

- The application is already configured to use `nexply` by default (`MONGODB_DATABASE`, overrideable through the environment).
- `nexply` currently has the `resume` application collection with one record; `jd` has not been materialized yet. GridFS uses the supporting `document_files.files` and `document_files.chunks` collections.
- The existing `nexus_ai.documents` record and its original GridFS file are still present. No migration or deletion was performed.
- The `nexply` resume record `6adda9b650f84544a4aabea5` has parsed text and now has a structured result; `llm_status=completed` and `llm_error` is cleared.

## API test run

- Swagger UI and `/openapi.json` both returned HTTP 200; OpenAPI lists the health, resume upload, parse, extract, and get routes.
- `python -m pytest -q`: 8 passed. These tests mock persistence and extraction, so they do not create MongoDB records or call Ollama.
- The existing resume's Ollama extraction was also exercised separately through the API and completed successfully after the thinking/schema fix.

## Storage target

Keep application records in `nexply.resume` and `nexply.jd`, with complete `parsed_text` and validated `structured_result` stored inline. Keep only uploaded originals in the `document_files` GridFS bucket. Preserve `nexus_ai` during the transition.
