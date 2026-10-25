# NEXPLY core test report

Date: 2026-10-25

## Result

- `python -m pytest -q`: **38 passed, 1 warning**.
- Live Swagger/OpenAPI and resume endpoint flow: **upload 201, parse 200, extract 200, get 200**.
- Live model extraction returned `llm_status=completed` and matched the fictional fixture's name, email, Python, MongoDB, education, employer, and project.
- Direct Ollama extraction of the fictional fixture now returns the canonical complete profile and preserves all fixture facts: name, email, phone, location, summary, 5 skills, education, job dates and both responsibility bullets, project, certification, and language.
- PDF hyperlink annotations on the existing local resume were read directly; LinkedIn, GitHub profile, LeetCode, and Portfolio URLs were detected without sending the document to an external service. GitHub repository links are excluded from the profile-link chips.
- The end-to-end run used `nexply_human_test`; the temporary database was dropped and the test server was stopped. Existing `nexply` data was not used for the run.

## Coverage

- File parser: UTF-8 TXT with BOM, DOCX paragraphs, multi-page PDF markers, empty DOCX, unsupported extension, and textless/scanned PDF behavior.
- Resume schema: optional-field defaults and required project name.
- Ollama adapter: JSON-schema request settings, no-thinking mode, empty/truncated output, invalid JSON, schema errors, and blank-input rejection. Ollama calls are mocked in unit tests.
- Job parser: case-insensitive aliases, deduplication, whole-word matching, normalized fields, and whitespace-only validation.
- API: OpenAPI paths, root, health, upload validation, parse/extract response handling, get response, and legacy router import. Storage and model calls are mocked in API unit tests.
- React + TypeScript UI: Vite production build, bundle serving, upload configuration, searchable structured profile table, and full-JSON export.
- Resume schema: complete standard sections, custom section retention (including string/object detail normalization), nested detail aliases, literal contact recovery, and omitted experience date recovery.
- PDF parser and resume extraction: embedded profile links are retained as clickable canonical website values; the Ollama prompt is loaded from `core/prompts/resume_extraction.py`.
- End-to-end: actual upload, parse, Ollama extraction, retrieval, inline MongoDB fields, original GridFS storage, and omission of the GridFS id from the GET response.

## Issues found and fixed

1. A PDF with no extractable text was accepted because page-marker text made the result look non-empty. The parser now rejects textless PDFs with the existing scanned/empty-file error.
2. Whitespace-only job fields passed Pydantic length validation. `JobInput` now strips whitespace before validation, so these inputs fail validation.
3. The job skill list did not include MongoDB. Added the canonical `MongoDB` alias.
4. The unused legacy `api/routes/resumes.py` module could not import because it looked for `extract_text` under storage. It now imports the core parser; its two route functions also have debug tracing.

## Remaining notes

- Scanned PDFs still need OCR to extract their image text; they now fail clearly instead of appearing to parse successfully.
- The skill extractor is dictionary-based, so skills absent from `SKILL_ALIASES` will not be recognized automatically.
- Pytest reports a Starlette deprecation warning: its `TestClient` currently uses `httpx`; the warning recommends `httpx2`. The tests pass despite this warning.
- The legacy `api/routes/resumes.py` implementation remains separate and is not mounted by `api/main.py`; keep it aligned or remove it when consolidating routes.
