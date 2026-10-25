# NEXPLY API endpoint tracker

Last reviewed: 2026-10-25

`Implemented` describes whether the route exists in the current application. `Tested` records a manual request made against the local app; a failed request stays visible as a failure rather than being marked complete.

| Endpoint | Implemented | Tested | Current result / next step |
|---|---|---|---|
| `GET /` | Yes | Yes | 200; app reports running. |
| `GET /health` | Yes | Yes | 200; local MongoDB ping succeeds and reports `nexply`. |
| `POST /resumes/upload` | Yes | No | Needs a controlled upload request and verification in `nexply.resume` plus `document_files`. |
| `GET /resumes/{document_id}` | Yes | Yes | 200 for existing resume `6adda9b650f84544a4aabea5`; parsed text is returned with 5,215 characters. |
| `POST /resumes/{document_id}/parse` | Yes | No (current record already parsed) | Parser was directly checked against the 740,848-byte PDF: 3 pages and 5,215 characters. The API parse path still needs a fresh controlled record before it can be marked tested. |
| `POST /resumes/{document_id}/extract` | Yes | Yes, failed | Existing record `6adda9b650f84544a4aabea5` has `llm_status=failed`; Ollama output did not validate against `ResumeData`. Diagnose the returned shape before retesting. |
| Job description upload/create endpoint | No | No | `jd` repository/service helpers exist, but there is no upload/create route wired into `main.py`. |
| Job description parse endpoint | No | No | `save_parsed_jd()` exists, but no file-backed parse flow or route is wired in. |
| Job description get endpoint | No | No | Repository lookup helper exists, but no route is wired in. |

## Database state checked

- The application is already configured to use `nexply` by default (`MONGODB_DATABASE`, overrideable through the environment).
- `nexply` currently has the `resume` application collection with one record; `jd` has not been materialized yet. GridFS uses the supporting `document_files.files` and `document_files.chunks` collections.
- The existing `nexus_ai.documents` record and its original GridFS file are still present. No migration or deletion was performed.
- The `nexply` resume record has parsed text and no structured result yet. The LLM error is recorded as `Ollama returned a response that does not match the resume schema.`

## Storage target

Keep application records in `nexply.resume` and `nexply.jd`, with complete `parsed_text` and validated `structured_result` stored inline. Keep only uploaded originals in the `document_files` GridFS bucket. Preserve `nexus_ai` during the transition.
