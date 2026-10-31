# NEXPLY Project File Index

This is the maintained file-by-file guide to the NEXPLY repository. Each first-party file and local project artifact in the current tree is listed below with its purpose. Update the relevant entry whenever a file is added, renamed, moved, repurposed, or removed.

## Inventory scope and maintenance

- Includes project source, tests, documentation, configuration, lockfiles, the local `.env` filename, and root-level local artifacts.
- Excludes generated/dependency trees: `.git`, `.venv`, `venv`, `node_modules`, `.pytest_cache`, `__pycache__`, `dist`, `build`, `.mypy_cache`, and `.ruff_cache`. These contain generated files rather than maintained project source.
- `.env` is intentionally listed by name only. Never copy its contents or secrets into this document.
- After changing the tree, update this index and run `python scripts/verify_file_index.py`. The checker detects missing or stale file entries; review descriptions manually when a file's purpose changes.

## Root configuration, documentation, and local artifacts

| File | Purpose |
|---|---|
| `.env` | Local, ignored runtime configuration for secrets and machine-specific settings. Its values are not documented here. |
| `.env.example` | Environment-variable template for the API and its dependencies; keep credentials as placeholders and never copy real secrets into it. |
| `requirements.txt` | Python runtime and development dependencies installed into the backend environment. |
| `run.py` | Convenience entry point for starting the FastAPI application from the source tree. |
| `CORE_TEST_REPORT.md` | Recorded results and notes from the backend's core verification pass. |
| `ENDPOINT_TRACKER.md` | Endpoint inventory and implementation/testing status tracker. |
| `PROJECT_FILE_INDEX.md` | This maintained, grouped purpose reference for every in-scope file. |
| `resume_from_mongodb.pdf` | Local PDF artifact used for resume extraction or preview work; not application source. |
| `docs/AUTHENTICATION_SETUP.md` | Setup guide for PostgreSQL authentication, schema prerequisites, and local auth configuration. |
| `docs/retrieval_evaluation/PHASE_5_REPORT.md` | Phase 5 retrieval evaluation findings, preliminary baseline, methodology caveats, decisions, and remaining acceptance work. |
| `docs/retrieval_evaluation/reports/retrieval_baseline.json` | Machine-readable live baseline metrics; candidate identifiers and profile text are excluded. |
| `docs/retrieval_evaluation/reports/retrieval_baseline.md` | Human-readable live baseline summary by score threshold and query category. |
| `scripts/verify_file_index.py` | Checks that every in-scope file is represented in this index and flags stale entries. |
| `scripts/update_file_flow_map.py` | Rebuilds the direct-import connection map below from current Python, TypeScript, and CSS imports. |

## Backend: application startup and HTTP API

| File | Purpose |
|---|---|
| `src/nexus/__init__.py` | Marks the top-level Python package. |
| `src/nexus/api/__init__.py` | Marks the API package. |
| `src/nexus/api/main.py` | Builds the FastAPI app, configures middleware/static frontend behavior, and registers routers and lifecycle hooks. |
| `src/nexus/api/auth.py` | Authentication request/response schemas, registration/sign-in/password-recovery routes, token validation, and current-user dependency. |
| `src/nexus/api/routes/__init__.py` | Marks the top-level API routes package. |
| `src/nexus/api/routes/health.py` | Health/status endpoint used to check API availability. |
| `src/nexus/api/routes/jds.py` | Authenticated job-description endpoints for upload, parsing, extraction, and retrieval. |
| `src/nexus/api/routes/resumes.py` | Compatibility/legacy resume router exposing upload and parse behavior for existing callers. |
| `src/nexus/api/routes/resume/__init__.py` | Combines the focused resume route modules into the resume API router. |
| `src/nexus/api/routes/resume/upload.py` | Validates and stores a user's latest resume upload, including request idempotency and ownership metadata. |
| `src/nexus/api/routes/resume/parse.py` | Parses the authenticated owner's original resume and stores extracted text/status. |
| `src/nexus/api/routes/resume/extract.py` | Runs structured resume extraction and persists/synchronizes the validated profile. |
| `src/nexus/api/routes/resume/get.py` | Retrieves resume details and original-file content with owner checks. |
| `src/nexus/api/routes/resume/history.py` | Serves the current/selected profile, profile edits, deletion, and job-preference API operations. |
| `src/nexus/api/routes/resume/ai.py` | REX interview, field rewrite, model listing, AI resume generation, and DOCX export routes. |

## Backend: core parsing, extraction, normalization, and schemas

| File | Purpose |
|---|---|
| `src/nexus/core/__init__.py` | Marks the backend core package. |
| `src/nexus/core/config.py` | Loads and validates environment-backed application, MongoDB, PostgreSQL, upload, JWT, SMTP, and Ollama settings. |
| `src/nexus/core/debug.py` | Provides reusable function tracing/debug logging decorators. |
| `src/nexus/core/parser.py` | Extracts source text from supported PDF, DOCX, and TXT documents. |
| `src/nexus/core/jd_extractor.py` | Calls the configured language model to turn job-description text into structured data. |
| `src/nexus/core/resume_extractor.py` | Coordinates resume extraction, schema validation, normalization, and public extraction helpers. |
| `src/nexus/core/resume_extraction_ollama.py` | Sends resume extraction prompts to Ollama and validates/decodes its structured response. |
| `src/nexus/core/resume_normalization.py` | Exposes the profile normalization pipeline used before validation and persistence. |
| `src/nexus/core/resume_normalize_common.py` | Shared value cleanup, alias, and normalization utilities for resume profile fields. |
| `src/nexus/core/resume_normalize_root.py` | Normalizes top-level candidate fields and profile metadata. |
| `src/nexus/core/resume_normalize_education.py` | Normalizes education entries and legacy education date/location/grade aliases. |
| `src/nexus/core/resume_normalize_projects.py` | Normalizes project entries and their names, dates, links, technologies, and descriptions. |
| `src/nexus/core/resume_normalize_sections.py` | Normalizes repeatable and custom resume sections while preserving their source titles/details. |
| `src/nexus/core/resume_source_contact.py` | Extracts contact and location facts from source resume text. |
| `src/nexus/core/resume_source_experience.py` | Extracts and reconciles work-history locations and experience facts from source text. |
| `src/nexus/core/resume_source_links.py` | Finds and normalizes candidate profile links from source text. |
| `src/nexus/core/schemas/__init__.py` | Marks the Pydantic schemas package. |
| `src/nexus/core/schemas/resume.py` | Defines the validated ResumeData contract and nested education, work, project, and custom-section models. |
| `src/nexus/core/prompts/__init__.py` | Marks the prompt package used by language-model tasks. |
| `src/nexus/core/prompts/resume_extraction.py` | Stores the full-source resume extraction prompt and JSON/schema response instructions. |
| `src/nexus/core/prompts/resume_writing.py` | Stores REX prompt templates for resume writing, conversational profile collection, and content rewriting. |
| `src/nexus/nlp/job_parser.py` | Parses job-description text into normalized skills, requirements, and role information. |

## Backend: application services and resume document generation

| File | Purpose |
|---|---|
| `src/nexus/services/__init__.py` | Marks the application services package. |
| `src/nexus/services/resume_service.py` | Coordinates resume lifecycle operations, GridFS cleanup, parsing/extraction, and PostgreSQL profile synchronization. |
| `src/nexus/services/jd_service.py` | Coordinates job-description persistence and processing. |
| `src/nexus/services/resume_writer.py` | Public facade for REX model discovery, interview, rewrite, and resume-generation services. |
| `src/nexus/services/resume_writer_common.py` | Shared Ollama request, parsing, and response helpers for resume-writing services. |
| `src/nexus/services/resume_model_catalog.py` | Lists and selects locally available Ollama models appropriate for resume writing. |
| `src/nexus/services/resume_interview.py` | Maintains the REX conversational flow that collects candidate details and follow-up answers. |
| `src/nexus/services/resume_rewrite.py` | Rewrites an individual profile field in concise, brief, or detailed styles. |
| `src/nexus/services/resume_generation.py` | Generates a complete resume draft from structured candidate data and optional job context. |
| `src/nexus/services/resume_export.py` | Public facade for generating a downloadable resume document. |
| `src/nexus/services/resume_docx_builder.py` | Assembles the final DOCX document from a validated structured profile. |
| `src/nexus/services/resume_docx_text.py` | Provides DOCX text, paragraph, and formatting helpers. |
| `src/nexus/services/resume_docx_components.py` | Builds reusable DOCX elements such as paragraphs, bullets, and section headings. |
| `src/nexus/services/resume_docx_header.py` | Renders candidate name and contact information at the top of the DOCX. |
| `src/nexus/services/resume_docx_sections.py` | Renders standard profile sections such as summary, experience, education, and skills. |
| `src/nexus/services/resume_docx_projects.py` | Renders project entries in the exported resume. |
| `src/nexus/services/resume_docx_additional.py` | Renders certificates, publications, awards, interests, and custom sections in the DOCX. |

## Backend: persistence and storage adapters

| File | Purpose |
|---|---|
| `src/nexus/storage/__init__.py` | Marks the storage adapter package. |
| `src/nexus/storage/mongodb.py` | Public facade exposing MongoDB collections, GridFS bucket, and resume upload persistence helpers. |
| `src/nexus/storage/mongodb_runtime.py` | Creates and configures the MongoDB client, database, collections, and GridFS bucket. |
| `src/nexus/storage/mongodb_upload.py` | Writes original uploads to GridFS and creates owned resume metadata records with idempotency support. |
| `src/nexus/storage/resume_repository.py` | Owner-scoped MongoDB queries and updates for resume profile documents. |
| `src/nexus/storage/jd_repository.py` | Owner-scoped MongoDB queries and updates for job-description documents. |
| `src/nexus/storage/postgres.py` | Public PostgreSQL facade for account, profile, preference, and password-recovery persistence. |
| `src/nexus/storage/postgres_accounts.py` | Creates and retrieves PostgreSQL user accounts and app IDs. |
| `src/nexus/storage/postgres_profiles.py` | Upserts the structured candidate-profile mirror and tracks its MongoDB source document. |
| `src/nexus/storage/postgres_preferences.py` | Reads and upserts each user's single job-preferences row. |
| `src/nexus/storage/postgres_password_recovery.py` | Stores OTP/reset-token challenges and safely replaces account passwords after verification. |
| `src/nexus/storage/parser.py` | Storage-facing parser compatibility module that exposes document text extraction. |

## Frontend: app boot, routing, authentication, and API utilities

| File | Purpose |
|---|---|
| `frontend/index.html` | Vite HTML shell that loads the React application. |
| `frontend/package.json` | Frontend scripts and direct JavaScript/TypeScript dependencies. |
| `frontend/package-lock.json` | Locked dependency tree for reproducible frontend installs. |
| `frontend/vite.config.ts` | Vite development/build configuration and API proxy settings. |
| `frontend/tsconfig.json` | Root TypeScript project references for app and tooling configs. |
| `frontend/tsconfig.app.json` | TypeScript compiler settings for browser application source. |
| `frontend/tsconfig.node.json` | TypeScript compiler settings for Node-based frontend tooling. |
| `frontend/README.md` | Frontend-specific setup and development notes. |
| `frontend/public/nexply.svg` | NEXPLY brand mark served as a static frontend asset. |
| `frontend/src/vite-env.d.ts` | Vite client type declarations for TypeScript. |
| `frontend/src/main.tsx` | React browser entry point that mounts the application. |
| `frontend/src/App.tsx` | Top-level app composition and page selection entry point. |
| `frontend/src/app/types.ts` | Shared frontend app layout/router type definitions. |
| `frontend/src/app/AppRouter.tsx` | Chooses the authenticated app view or sign-in/create-account flow. |
| `frontend/src/app/AppLayout.tsx` | Renders the authenticated application shell and navigation. |
| `frontend/src/Auth.tsx` | Coordinates authentication state, API calls, session persistence, and auth actions. |
| `frontend/src/AuthView.tsx` | Renders the sign-in, registration, and password-reset screens. |
| `frontend/src/authTypes.ts` | Shared TypeScript types for authenticated users and auth view state. |
| `frontend/src/shared/api.ts` | Central HTTP client that attaches auth credentials and handles API errors. |

## Frontend: profile, resume editing, and REX components

| File | Purpose |
|---|---|
| `frontend/src/pages/ProfilePage.tsx` | Composes the profile workspace, resume upload, preferences, and editable profile panels. |
| `frontend/src/pages/ProfileWorkspacePanels.tsx` | Renders the profile heading, empty/start state, editable fields panel, and workspace footer. |
| `frontend/src/pages/ResumeSourceCard.tsx` | Handles resume selection/drop, original-file preview, extraction status, and upload actions. |
| `frontend/src/pages/ProfilePreferences.tsx` | Edits and saves job-search preferences such as compensation, location, role, and availability. |
| `frontend/src/pages/profile-preferences-model.ts` | Defines the job-preferences data type, defaults, and display helpers. |
| `frontend/src/pages/profileWorkspaceTypes.ts` | Defines shared types for resume processing phases and API records. |
| `frontend/src/pages/useApiAvailability.ts` | Checks backend availability and retrieves upload-size limits for the workspace. |
| `frontend/src/pages/useJobPreferences.ts` | Loads, edits, and persists the user's PostgreSQL job-preferences row. |
| `frontend/src/pages/useProfileEditor.ts` | Applies nested profile edits and saves profile changes to the backend. |
| `frontend/src/pages/useProfileRecord.ts` | Loads the user's latest profile and owns its document, source, and processing state. |
| `frontend/src/pages/useResumeExtraction.ts` | Runs the upload/parse/extract sequence and updates profile state with the result. |
| `frontend/src/pages/useResumeFile.ts` | Manages selected resume file state, validation, preview URLs, and reset behavior. |
| `frontend/src/components/ResumeEditor.tsx` | Provides the full block-based resume editor and save/cancel controls. |
| `frontend/src/components/ResumeEditorFields.tsx` | Renders field groups and repeatable entries for the structured resume sections. |
| `frontend/src/components/ResumePreview.tsx` | Shows a live rendered resume preview from the structured profile. |
| `frontend/src/components/resumeEditorActions.ts` | Implements shared editor field update, add, remove, and custom-section actions. |
| `frontend/src/components/RichTextEditor.tsx` | Rich-text editing controls for resume descriptions and narrative fields. |
| `frontend/src/components/RichTextContent.tsx` | Safely renders formatted resume text in previews and display panels. |
| `frontend/src/components/RexResumeBuilder.tsx` | Generates and exports AI-assisted resume drafts through REX. |
| `frontend/src/components/RexManualProfile.tsx` | Runs the conversational REX flow for building a profile manually. |
| `frontend/src/shared/resumeFormat.tsx` | Shared resume profile types, formatting functions, and structured section display helpers. |
| `frontend/src/shared/ResumeDetailRows.tsx` | Displays labeled profile detail rows while omitting unavailable values. |

## Frontend: stylesheets

| File | Purpose |
|---|---|
| `frontend/src/styles.css` | Imports the ordered feature stylesheets and defines shared global style entry points. |
| `frontend/src/styles/design-tokens-and-rex-chat.css` | Defines global design tokens and REX chat presentation styles. |
| `frontend/src/styles/app-shell-and-navigation.css` | Styles the authenticated app shell, top-level navigation, and shared page framing. |
| `frontend/src/styles/authentication-layout.css` | Styles auth page structure, branding, and responsive layout. |
| `frontend/src/styles/authentication-controls.css` | Styles auth forms, validation feedback, buttons, and password-reset controls. |
| `frontend/src/styles/profile-workspace.css` | Styles the main profile workspace and upload/preferences columns. |
| `frontend/src/styles/resume-upload-workspace.css` | Styles file drop zones, selected files, upload state, and extraction progress. |
| `frontend/src/styles/manual-profile-builder.css` | Styles manual profile editing blocks and repeatable section cards. |
| `frontend/src/styles/resume-entry-editor.css` | Styles individual resume-entry editors, rich-text controls, and field layouts. |
| `frontend/src/styles/profile-editor-toolbar.css` | Styles formatting and action toolbars in the profile editor. |
| `frontend/src/styles/resume-preview.css` | Styles the on-screen resume preview and print/export presentation. |
| `frontend/src/styles/history-profile.css` | Styles structured profile/history detail presentation retained by supporting views. |
| `frontend/src/styles/ai-tools-and-progress.css` | Styles AI/REX actions, model feedback, loading indicators, and progress states. |

## Tests: shared fixtures

| File | Purpose |
|---|---|
| `tests/fixtures/mock_resume.txt` | Small representative resume fixture for parser and extraction tests. |

## Tests: authentication and account security

| File | Purpose |
|---|---|
| `tests/test_account_registration.py` | Covers account creation, app ID assignment, and account persistence behavior. |
| `tests/test_registration_validation.py` | Checks registration input validation and password confirmation requirements. |
| `tests/test_login_and_session.py` | Covers successful sign-in and authenticated session/token behavior. |
| `tests/test_login_and_signing.py` | Verifies password checks, token issuance, and signing configuration. |
| `tests/test_token_and_owner_scoping.py` | Rejects invalid tokens and verifies Mongo reads/updates are scoped by app ID. |
| `tests/test_route_authentication_api.py` | Confirms protected API routes require valid authentication. |

## Tests: resume upload, parsing, ownership, and deletion

| File | Purpose |
|---|---|
| `tests/test_resume_upload_api.py` | Validates resume upload API behavior and response metadata. |
| `tests/test_upload_idempotency.py` | Checks duplicate upload request keys and stable result handling. |
| `tests/test_concurrent_upload_idempotency.py` | Exercises idempotent behavior under overlapping upload attempts. |
| `tests/test_upload_owner_metadata.py` | Verifies uploaded GridFS files and Mongo records carry authenticated owner metadata. |
| `tests/test_resume_parse_and_extract_api.py` | Covers the resume parse and structured extraction API sequence. |
| `tests/test_document_text_extraction.py` | Validates text extraction for supported source document formats. |
| `tests/test_resume_source_recovery.py` | Checks behavior when original uploaded source files are missing or recoverable. |
| `tests/test_resume_repository_ownership.py` | Confirms resume repository reads/updates enforce owner scoping. |
| `tests/test_resume_retrieval_api.py` | Covers authenticated resume retrieval and response shaping. |
| `tests/test_resume_delete_api.py` | Verifies resume deletion API behavior for the authenticated owner. |
| `tests/test_resume_gridfs_cleanup.py` | Checks GridFS originals are removed when their Mongo resume record is deleted. |
| `tests/test_resume_and_jd_owner_fields.py` | Verifies owner identifiers are assigned to resume and job-description records. |

## Tests: structured profiles, SQL sync, and preferences

| File | Purpose |
|---|---|
| `tests/test_latest_profile_normalization_api.py` | Checks latest profile alias normalization and Mongo/PostgreSQL synchronization. |
| `tests/test_education_legacy_aliases.py` | Covers canonical education date, location, grade, and award field mappings. |
| `tests/test_profile_alias_normalization.py` | Tests profile-wide legacy alias cleanup and canonical output shape. |
| `tests/test_structured_profile_update_api.py` | Verifies owner-scoped in-place updates to structured resume profile data. |
| `tests/test_profile_owner_access_api.py` | Checks users can access only their own profile and resume data. |
| `tests/test_profile_schema_and_sql_sync.py` | Validates profile schema conversion and the PostgreSQL mirror sync. |
| `tests/test_postgres_profile_upserts.py` | Checks one-row-per-app-ID upserts for structured candidate profiles. |
| `tests/test_candidate_profile_source_lookup.py` | Verifies owner-scoped PostgreSQL lookup of the Mongo source document linked to a candidate profile. |
| `tests/test_job_preferences_api.py` | Covers preference loading/saving and the single-row-per-user contract. |
| `tests/test_manual_profile_save_api.py` | Validates manually created profiles and their persisted resume records. |

## Tests: REX, Ollama, export, and API documentation

| File | Purpose |
|---|---|
| `tests/test_ollama_response_validation.py` | Checks malformed or schema-mismatched Ollama output is rejected safely. |
| `tests/test_profile_validation_and_ai_smart_api.py` | Covers profile validation and AI-assisted resume generation API behavior. |
| `tests/test_rex_rewrite_and_interview_api.py` | Validates REX field rewriting and conversational profile interview routes. |
| `tests/test_resume_export_api.py` | Checks DOCX resume export without creating duplicate profile records. |
| `tests/test_resume_link_and_ollama_request.py` | Validates source links and Ollama request construction/response behavior. |
| `tests/test_resume_api_docs.py` | Ensures resume API routes and schemas are represented in generated OpenAPI docs. |
| `tests/test_parser_and_schema_validation.py` | Tests parser output and structured resume schema validation. |
| `tests/test_job_parser.py` | Covers job-description parsing and normalized requirement extraction. |
| `tests/test_api_health_and_static_assets.py` | Checks health endpoint and frontend/static asset serving behavior. |

## Tests: candidate memory retrieval evaluation

| File | Purpose |
|---|---|
| `tests/retrieval_evaluation/README.md` | Documents dataset generation, live-run setup, metrics, privacy constraints, and the preliminary annotation limitation. |
| `tests/retrieval_evaluation/test_queries.json` | Candidate-local evaluation questions and memory-ID relevance labels; excludes app ID and memory text. Current labels are section-wide and preliminary. |
| `tests/retrieval_evaluation/query_catalog.py` | Defines the human-authored query set, categories, expected classifier intent/sections, and rationale. |
| `tests/retrieval_evaluation/dataset.py` | Builds and validates query annotation records and required category coverage. |
| `tests/retrieval_evaluation/build_local_dataset.py` | Binds the catalog to current candidate-owned Qdrant memory IDs without reading payload text. |
| `tests/retrieval_evaluation/scope_validation.py` | Verifies each expected memory ID belongs to the selected app ID and is a memory node. |
| `tests/retrieval_evaluation/metrics.py` | Implements Precision@K, Recall@K, MRR, and Hit Rate with duplicate and empty-result handling. |
| `tests/retrieval_evaluation/evaluation_runner.py` | Executes injected classifier/retriever functions and aggregates overall/category results and latency. |
| `tests/retrieval_evaluation/report_writer.py` | Writes privacy-minimized JSON and Markdown evaluation reports. |
| `tests/retrieval_evaluation/evaluate_retrieval.py` | CLI entry point for live classifier/retriever evaluation with candidate-owner validation. |
| `tests/retrieval_evaluation/test_evaluation_metrics.py` | Unit tests for ranking metrics, edge cases, and multiple cutoffs. |
| `tests/retrieval_evaluation/test_dataset_annotations.py` | Tests catalog binding and dataset field/category validation. |
| `tests/retrieval_evaluation/test_evaluation_runner.py` | Tests aggregation and runner outcomes with mocked classifier and retriever. |
| `tests/retrieval_evaluation/test_candidate_intent_classifier.py` | Tests Qwen classifier validation, regex fallback, section mappings, and invalid inputs. |
| `tests/retrieval_evaluation/test_candidate_retriever.py` | Tests candidate scoping, memory-node filtering, explicit sections, and threshold forwarding. |
| `tests/retrieval_evaluation/test_scope_validation.py` | Tests rejection of missing, non-memory, or cross-candidate relevance labels. |
| `tests/retrieval_evaluation/test_report_writer.py` | Tests generated report structure and privacy-safe output. |
| `tests/retrieval_evaluation/test_live_retrieval.py` | Optional environment-gated smoke test for local embedding and Qdrant retrieval. |
| `tests/retrieval_evaluation/__init__.py` | Marks the retrieval evaluation helpers as an importable Python package. |
| `tests/__init__.py` | Marks the test tree as an importable Python package for module-based evaluation commands. |

## End-to-end file flows

The arrows below follow the application from its entry point through the browser, API, service layer, and persistence. The generated map in the next section lists direct local imports per implementation file; the sequences here add runtime order and the work each layer performs.

### Candidate semantic memory and retrieval evaluation

Profile data enters `candidate_memory_builder.py` → `candidate_memory_tree.py` to produce candidate-root, section, and memory nodes; `candidate_memory_indexer.py` embeds and upserts those nodes using `embedding_service.py` into the existing Qdrant collection. At query time, `candidate_llm_intent_classifier.py` uses Qwen and falls back to `candidate_query_classifier.py`; `candidate_memory_retriever.py` embeds the question and filters Qdrant by authenticated `app_id`, `node_type=memory`, and (when specific) the validated `source_section`. The Phase 5 evaluation path is `query_catalog.py` → `build_local_dataset.py` / `dataset.py` → `scope_validation.py` → `evaluate_retrieval.py` → `evaluation_runner.py` → `metrics.py` → `report_writer.py`. The runner invokes the live classifier and retriever; mocked unit tests exercise it without local services. Reports under `docs/retrieval_evaluation/reports/` contain aggregate results and opaque point IDs only. The current dataset labels are section-wide, so the report is explicitly preliminary pending manual fact-level annotation.

### Browser startup and authenticated profile workspace

`frontend/index.html` loads `frontend/src/main.tsx` → `frontend/src/App.tsx` → `frontend/src/app/AppRouter.tsx`. The router checks the session through `frontend/src/shared/api.ts`, then renders `frontend/src/Auth.tsx` / `frontend/src/AuthView.tsx` for unauthenticated visitors or `frontend/src/app/AppLayout.tsx` with `frontend/src/pages/ProfilePage.tsx` for signed-in users. `ProfilePage.tsx` composes `ProfileWorkspacePanels.tsx`, `ResumeSourceCard.tsx`, `ProfilePreferences.tsx`, and the `use*` hooks. Those hooks call `shared/api.ts`; app styles enter at `frontend/src/main.tsx` and `frontend/src/styles.css`.

### Registration, sign-in, and password recovery

The browser auth form in `AuthView.tsx` collects data and `Auth.tsx` sends it through `shared/api.ts` to `src/nexus/api/auth.py`. The API validates inputs, hashes passwords, and uses `src/nexus/storage/postgres.py` plus the focused account and password-recovery adapters. Signed bearer tokens identify the account; protected routes call `get_current_user` and use the PostgreSQL account's `app_id` as the owner key. Password recovery additionally uses SMTP settings from `src/nexus/core/config.py` and single-use OTP/reset-token storage in PostgreSQL.

### Resume upload, extraction, and profile display

`ResumeSourceCard.tsx` → `useResumeFile.ts` → `useResumeExtraction.ts` → `shared/api.ts` → `routes/resume/upload.py` → `storage/mongodb.py` → `mongodb_upload.py` / `mongodb_runtime.py`. The original file is placed in GridFS and owner-scoped resume metadata is written to MongoDB. Parsing then flows through `routes/resume/parse.py` → `services/resume_service.py` → `core/parser.py` → `resume_repository.py`; extracted source text is saved on the same resume record. Structured extraction flows through `routes/resume/extract.py` → `resume_service.py` → `core/resume_extractor.py` → `resume_extraction_ollama.py` → prompt, normalization, and schema modules. The validated JSON updates MongoDB and is synchronized to PostgreSQL by `postgres_profiles.py`. `useProfileRecord.ts` loads the latest profile and `ResumeEditor.tsx` / `ResumePreview.tsx` render and edit it.

### Manual profile creation and REX features

`RexManualProfile.tsx` sends the conversation to `routes/resume/ai.py` → `services/resume_writer.py` → `resume_interview.py` and shared Ollama/prompt helpers. Saving the completed profile uses the manual-profile route, validates it with `schemas/resume.py`, creates a DOCX through `resume_export.py` and the `resume_docx_*` modules, stores the original in GridFS, and writes the structured profile to MongoDB and PostgreSQL. Field rewrites and generated drafts use `resume_rewrite.py` and `resume_generation.py`; `RexResumeBuilder.tsx` can request DOCX export without creating another resume record.

### Manual edits and job preferences

`ResumeEditor.tsx` and `ProfilePreferences.tsx` use `useProfileEditor.ts` and `useJobPreferences.ts` to submit changes. Structured edits update the existing MongoDB record through `routes/resume/history.py` and `resume_repository.py`, then synchronize the one-row-per-app-ID profile mirror through `resume_service.py` and `postgres_profiles.py`. Preferences use the same history route and `postgres_preferences.py`; MongoDB does not store job preferences.

### Job-description processing and deletion

Job-description endpoints in `routes/jds.py` pass through `jd_service.py`, `jd_extractor.py` / `nlp/job_parser.py`, `jd_repository.py`, and the configured MongoDB `jd` collection. Resume deletion passes from the profile UI to `routes/resume/history.py`, then `resume_service.py` deletes the owner-scoped MongoDB document and associated GridFS originals. The Mongo health endpoint checks MongoDB connectivity only; it does not imply that PostgreSQL, Ollama, or an external vector database is healthy.

## Direct file-level import connections

This table is generated from local imports (not inferred from filenames). It shows the direct implementation files each code file depends on; the flows above explain call order across those layers. Files with no local imports are still listed and described above. Configuration, documentation, and binary artifacts are not runtime-imported code.

<!-- BEGIN GENERATED FILE FLOW MAP -->

| File | Direct project file connections |
|---|---|
| `frontend/src/app/AppLayout.tsx` | `frontend/src/app/types.ts` |
| `frontend/src/app/AppRouter.tsx` | `frontend/src/app/AppLayout.tsx`, `frontend/src/app/types.ts`, `frontend/src/Auth.tsx`, `frontend/src/pages/ProfilePage.tsx`, `frontend/src/shared/api.ts` |
| `frontend/src/app/types.ts` | No direct local imports; see its role above. |
| `frontend/src/App.tsx` | `frontend/src/app/AppRouter.tsx` |
| `frontend/src/Auth.tsx` | `frontend/src/authTypes.ts`, `frontend/src/AuthView.tsx` |
| `frontend/src/authTypes.ts` | No direct local imports; see its role above. |
| `frontend/src/AuthView.tsx` | `frontend/src/authTypes.ts` |
| `frontend/src/components/ResumeEditor.tsx` | `frontend/src/components/resumeEditorActions.ts`, `frontend/src/components/ResumeEditorFields.tsx`, `frontend/src/components/ResumePreview.tsx`, `frontend/src/shared/api.ts`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/components/resumeEditorActions.ts` | `frontend/src/components/ResumeEditorFields.tsx`, `frontend/src/shared/api.ts`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/components/ResumeEditorFields.tsx` | `frontend/src/components/RichTextEditor.tsx`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/components/ResumePreview.tsx` | `frontend/src/components/RichTextEditor.tsx`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/components/RexManualProfile.tsx` | `frontend/src/shared/api.ts`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/components/RexResumeBuilder.tsx` | `frontend/src/components/ResumeEditor.tsx`, `frontend/src/shared/api.ts`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/components/RichTextContent.tsx` | `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/components/RichTextEditor.tsx` | `frontend/src/components/RichTextContent.tsx`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/main.tsx` | `frontend/src/app.tsx`, `frontend/src/styles.css` |
| `frontend/src/pages/profile-preferences-model.ts` | No direct local imports; see its role above. |
| `frontend/src/pages/ProfilePage.tsx` | `frontend/src/pages/ProfilePreferences.tsx`, `frontend/src/pages/ProfileWorkspacePanels.tsx`, `frontend/src/pages/ResumeSourceCard.tsx`, `frontend/src/pages/useApiAvailability.ts`, `frontend/src/pages/useJobPreferences.ts`, `frontend/src/pages/useProfileEditor.ts`, `frontend/src/pages/useProfileRecord.ts`, `frontend/src/pages/useResumeExtraction.ts`, `frontend/src/pages/useResumeFile.ts` |
| `frontend/src/pages/ProfilePreferences.tsx` | `frontend/src/pages/profile-preferences-model.ts` |
| `frontend/src/pages/ProfileWorkspacePanels.tsx` | `frontend/src/components/ResumeEditor.tsx`, `frontend/src/components/RexResumeBuilder.tsx`, `frontend/src/pages/useProfileEditor.ts`, `frontend/src/pages/useProfileRecord.ts`, `frontend/src/pages/useResumeFile.ts` |
| `frontend/src/pages/profileWorkspaceTypes.ts` | `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/pages/ResumeSourceCard.tsx` | `frontend/src/pages/profileWorkspaceTypes.ts`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/pages/useApiAvailability.ts` | `frontend/src/shared/api.ts` |
| `frontend/src/pages/useJobPreferences.ts` | `frontend/src/pages/profile-preferences-model.ts`, `frontend/src/shared/api.ts` |
| `frontend/src/pages/useProfileEditor.ts` | `frontend/src/shared/api.ts`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/pages/useProfileRecord.ts` | `frontend/src/pages/profileWorkspaceTypes.ts`, `frontend/src/shared/api.ts`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/pages/useResumeExtraction.ts` | `frontend/src/pages/profileWorkspaceTypes.ts`, `frontend/src/shared/api.ts`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/pages/useResumeFile.ts` | `frontend/src/pages/profileWorkspaceTypes.ts`, `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/shared/api.ts` | No direct local imports; see its role above. |
| `frontend/src/shared/ResumeDetailRows.tsx` | `frontend/src/shared/resumeFormat.tsx` |
| `frontend/src/shared/resumeFormat.tsx` | No direct local imports; see its role above. |
| `frontend/src/styles/ai-tools-and-progress.css` | No direct local imports; see its role above. |
| `frontend/src/styles/app-shell-and-navigation.css` | No direct local imports; see its role above. |
| `frontend/src/styles/authentication-controls.css` | No direct local imports; see its role above. |
| `frontend/src/styles/authentication-layout.css` | No direct local imports; see its role above. |
| `frontend/src/styles/design-tokens-and-rex-chat.css` | No direct local imports; see its role above. |
| `frontend/src/styles/history-profile.css` | No direct local imports; see its role above. |
| `frontend/src/styles/manual-profile-builder.css` | No direct local imports; see its role above. |
| `frontend/src/styles/profile-editor-toolbar.css` | No direct local imports; see its role above. |
| `frontend/src/styles/profile-workspace.css` | No direct local imports; see its role above. |
| `frontend/src/styles/resume-entry-editor.css` | No direct local imports; see its role above. |
| `frontend/src/styles/resume-preview.css` | No direct local imports; see its role above. |
| `frontend/src/styles/resume-upload-workspace.css` | No direct local imports; see its role above. |
| `frontend/src/styles.css` | `frontend/src/styles/ai-tools-and-progress.css`, `frontend/src/styles/app-shell-and-navigation.css`, `frontend/src/styles/authentication-controls.css`, `frontend/src/styles/authentication-layout.css`, `frontend/src/styles/design-tokens-and-rex-chat.css`, `frontend/src/styles/history-profile.css`, `frontend/src/styles/manual-profile-builder.css`, `frontend/src/styles/profile-editor-toolbar.css`, `frontend/src/styles/profile-workspace.css`, `frontend/src/styles/resume-entry-editor.css`, `frontend/src/styles/resume-preview.css`, `frontend/src/styles/resume-upload-workspace.css` |
| `frontend/src/vite-env.d.ts` | No direct local imports; see its role above. |
| `scripts/inspect_candidate_memory.py` | `src/nexus/services/candidate_memory_builder.py`, `src/nexus/storage/postgres.py` |
| `scripts/update_file_flow_map.py` | No direct local imports; see its role above. |
| `scripts/verify_file_index.py` | No direct local imports; see its role above. |
| `src/nexus/__init__.py` | No direct local imports; see its role above. |
| `src/nexus/api/__init__.py` | No direct local imports; see its role above. |
| `src/nexus/api/auth.py` | `src/nexus/core/config.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/postgres.py` |
| `src/nexus/api/main.py` | `src/nexus/api/auth.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py`, `src/nexus/core/config.py`, `src/nexus/core/debug.py` |
| `src/nexus/api/routes/__init__.py` | No direct local imports; see its role above. |
| `src/nexus/api/routes/health.py` | `src/nexus/core/debug.py`, `src/nexus/storage/mongodb.py` |
| `src/nexus/api/routes/jds.py` | No direct local imports; see its role above. |
| `src/nexus/api/routes/resume/__init__.py` | No direct local imports; see its role above. |
| `src/nexus/api/routes/resume/ai.py` | `src/nexus/api/auth.py`, `src/nexus/core/config.py`, `src/nexus/core/schemas/resume.py`, `src/nexus/services/resume_export.py`, `src/nexus/services/resume_service.py`, `src/nexus/services/resume_writer.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/resume_repository.py` |
| `src/nexus/api/routes/resume/extract.py` | `src/nexus/api/auth.py`, `src/nexus/core/debug.py`, `src/nexus/services/resume_service.py` |
| `src/nexus/api/routes/resume/get.py` | `src/nexus/api/auth.py`, `src/nexus/core/resume_extractor.py`, `src/nexus/services/resume_service.py` |
| `src/nexus/api/routes/resume/history.py` | `src/nexus/api/auth.py`, `src/nexus/core/resume_extractor.py`, `src/nexus/core/schemas/resume.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `src/nexus/api/routes/resume/parse.py` | `src/nexus/api/auth.py`, `src/nexus/core/debug.py`, `src/nexus/services/resume_service.py` |
| `src/nexus/api/routes/resume/upload.py` | `src/nexus/api/auth.py`, `src/nexus/core/config.py`, `src/nexus/core/debug.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/mongodb.py` |
| `src/nexus/api/routes/resumes.py` | `src/nexus/api/auth.py`, `src/nexus/core/debug.py`, `src/nexus/core/parser.py`, `src/nexus/storage/mongodb.py` |
| `src/nexus/core/__init__.py` | No direct local imports; see its role above. |
| `src/nexus/core/config.py` | No direct local imports; see its role above. |
| `src/nexus/core/debug.py` | No direct local imports; see its role above. |
| `src/nexus/core/jd_extractor.py` | No direct local imports; see its role above. |
| `src/nexus/core/parser.py` | `src/nexus/core/debug.py` |
| `src/nexus/core/prompts/__init__.py` | No direct local imports; see its role above. |
| `src/nexus/core/prompts/resume_extraction.py` | No direct local imports; see its role above. |
| `src/nexus/core/prompts/resume_writing.py` | No direct local imports; see its role above. |
| `src/nexus/core/resume_extraction_ollama.py` | `src/nexus/core/config.py`, `src/nexus/core/debug.py`, `src/nexus/core/prompts/resume_extraction.py`, `src/nexus/core/resume_normalization.py`, `src/nexus/core/resume_source_contact.py`, `src/nexus/core/resume_source_experience.py`, `src/nexus/core/resume_source_links.py`, `src/nexus/core/schemas/resume.py` |
| `src/nexus/core/resume_extractor.py` | `src/nexus/core/resume_extraction_ollama.py`, `src/nexus/core/resume_normalization.py`, `src/nexus/core/resume_source_contact.py`, `src/nexus/core/resume_source_experience.py`, `src/nexus/core/resume_source_links.py` |
| `src/nexus/core/resume_normalization.py` | `src/nexus/core/resume_normalize_education.py`, `src/nexus/core/resume_normalize_projects.py`, `src/nexus/core/resume_normalize_root.py`, `src/nexus/core/resume_normalize_sections.py` |
| `src/nexus/core/resume_normalize_common.py` | No direct local imports; see its role above. |
| `src/nexus/core/resume_normalize_education.py` | `src/nexus/core/resume_normalize_common.py` |
| `src/nexus/core/resume_normalize_projects.py` | `src/nexus/core/resume_normalize_common.py` |
| `src/nexus/core/resume_normalize_root.py` | `src/nexus/core/resume_normalize_common.py` |
| `src/nexus/core/resume_normalize_sections.py` | `src/nexus/core/resume_normalize_common.py`, `src/nexus/core/schemas/resume.py` |
| `src/nexus/core/resume_source_contact.py` | No direct local imports; see its role above. |
| `src/nexus/core/resume_source_experience.py` | `src/nexus/core/debug.py` |
| `src/nexus/core/resume_source_links.py` | `src/nexus/core/debug.py` |
| `src/nexus/core/schemas/__init__.py` | No direct local imports; see its role above. |
| `src/nexus/core/schemas/resume.py` | No direct local imports; see its role above. |
| `src/nexus/nlp/job_parser.py` | `src/nexus/core/debug.py` |
| `src/nexus/services/__init__.py` | No direct local imports; see its role above. |
| `src/nexus/services/candidate_llm_intent_classifier.py` | `src/nexus/services/candidate_query_classifier.py` |
| `src/nexus/services/candidate_memory_builder.py` | No direct local imports; see its role above. |
| `src/nexus/services/candidate_memory_indexer.py` | `src/nexus/services/embedding_service.py` |
| `src/nexus/services/candidate_memory_retriever.py` | `src/nexus/services/candidate_llm_intent_classifier.py`, `src/nexus/services/embedding_service.py` |
| `src/nexus/services/candidate_memory_tree.py` | `src/nexus/services/candidate_memory_builder.py` |
| `src/nexus/services/candidate_query_classifier.py` | No direct local imports; see its role above. |
| `src/nexus/services/embedding_service.py` | No direct local imports; see its role above. |
| `src/nexus/services/jd_service.py` | `src/nexus/core/debug.py`, `src/nexus/storage/jd_repository.py` |
| `src/nexus/services/resume_docx_additional.py` | `src/nexus/services/resume_docx_components.py` |
| `src/nexus/services/resume_docx_builder.py` | `src/nexus/core/debug.py`, `src/nexus/core/schemas/resume.py`, `src/nexus/services/resume_docx_additional.py`, `src/nexus/services/resume_docx_header.py`, `src/nexus/services/resume_docx_projects.py`, `src/nexus/services/resume_docx_sections.py` |
| `src/nexus/services/resume_docx_components.py` | `src/nexus/services/resume_docx_text.py` |
| `src/nexus/services/resume_docx_header.py` | `src/nexus/services/resume_docx_components.py` |
| `src/nexus/services/resume_docx_projects.py` | `src/nexus/services/resume_docx_components.py` |
| `src/nexus/services/resume_docx_sections.py` | `src/nexus/services/resume_docx_components.py` |
| `src/nexus/services/resume_docx_text.py` | No direct local imports; see its role above. |
| `src/nexus/services/resume_export.py` | `src/nexus/services/resume_docx_builder.py` |
| `src/nexus/services/resume_generation.py` | `src/nexus/services/resume_model_catalog.py`, `src/nexus/services/resume_writer_common.py` |
| `src/nexus/services/resume_interview.py` | `src/nexus/services/resume_model_catalog.py`, `src/nexus/services/resume_writer_common.py` |
| `src/nexus/services/resume_model_catalog.py` | `src/nexus/services/resume_writer_common.py` |
| `src/nexus/services/resume_rewrite.py` | `src/nexus/services/resume_model_catalog.py`, `src/nexus/services/resume_writer_common.py` |
| `src/nexus/services/resume_service.py` | `src/nexus/core/debug.py`, `src/nexus/core/parser.py`, `src/nexus/core/resume_extractor.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `src/nexus/services/resume_writer.py` | `src/nexus/services/resume_generation.py`, `src/nexus/services/resume_interview.py`, `src/nexus/services/resume_model_catalog.py`, `src/nexus/services/resume_rewrite.py` |
| `src/nexus/services/resume_writer_common.py` | `src/nexus/core/config.py`, `src/nexus/core/debug.py`, `src/nexus/core/prompts/resume_writing.py`, `src/nexus/core/schemas/resume.py` |
| `src/nexus/storage/__init__.py` | No direct local imports; see its role above. |
| `src/nexus/storage/jd_repository.py` | `src/nexus/core/debug.py`, `src/nexus/storage/mongodb.py` |
| `src/nexus/storage/mongodb.py` | `src/nexus/core/debug.py`, `src/nexus/storage/mongodb_runtime.py`, `src/nexus/storage/mongodb_upload.py` |
| `src/nexus/storage/mongodb_runtime.py` | `src/nexus/core/config.py`, `src/nexus/core/debug.py` |
| `src/nexus/storage/mongodb_upload.py` | `src/nexus/core/debug.py`, `src/nexus/storage/mongodb_runtime.py` |
| `src/nexus/storage/parser.py` | `src/nexus/core/debug.py`, `src/nexus/services/resume_service.py` |
| `src/nexus/storage/postgres.py` | `src/nexus/core/config.py`, `src/nexus/core/debug.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/postgres_accounts.py`, `src/nexus/storage/postgres_password_recovery.py`, `src/nexus/storage/postgres_preferences.py`, `src/nexus/storage/postgres_profiles.py` |
| `src/nexus/storage/postgres_accounts.py` | No direct local imports; see its role above. |
| `src/nexus/storage/postgres_password_recovery.py` | No direct local imports; see its role above. |
| `src/nexus/storage/postgres_preferences.py` | No direct local imports; see its role above. |
| `src/nexus/storage/postgres_profiles.py` | No direct local imports; see its role above. |
| `src/nexus/storage/resume_repository.py` | `src/nexus/core/debug.py`, `src/nexus/storage/mongodb.py` |
| `tests/__init__.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/__init__.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/build_local_dataset.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/dataset.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/evaluate_retrieval.py` | `src/nexus/services/__init__.py`, `src/nexus/services/candidate_llm_intent_classifier.py`, `src/nexus/services/candidate_memory_retriever.py` |
| `tests/retrieval_evaluation/evaluation_runner.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/metrics.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/query_catalog.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/report_writer.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/scope_validation.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/test_candidate_intent_classifier.py` | `src/nexus/services/__init__.py`, `src/nexus/services/candidate_llm_intent_classifier.py`, `src/nexus/services/candidate_query_classifier.py` |
| `tests/retrieval_evaluation/test_candidate_retriever.py` | `src/nexus/services/__init__.py`, `src/nexus/services/candidate_memory_retriever.py` |
| `tests/retrieval_evaluation/test_dataset_annotations.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/test_evaluation_metrics.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/test_evaluation_runner.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/test_live_retrieval.py` | `src/nexus/services/candidate_memory_retriever.py`, `src/nexus/services/embedding_service.py` |
| `tests/retrieval_evaluation/test_report_writer.py` | No direct local imports; see its role above. |
| `tests/retrieval_evaluation/test_scope_validation.py` | No direct local imports; see its role above. |
| `tests/test_account_registration.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `tests/test_api_health_and_static_assets.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_candidate_profile_source_lookup.py` | `src/nexus/storage/__init__.py`, `src/nexus/storage/postgres.py` |
| `tests/test_concurrent_upload_idempotency.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `tests/test_document_text_extraction.py` | `src/nexus/api/routes/resumes.py`, `src/nexus/core/__init__.py`, `src/nexus/core/parser.py`, `src/nexus/core/prompts/resume_extraction.py`, `src/nexus/core/resume_extractor.py`, `src/nexus/core/schemas/resume.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py` |
| `tests/test_education_legacy_aliases.py` | `src/nexus/api/routes/resumes.py`, `src/nexus/core/__init__.py`, `src/nexus/core/parser.py`, `src/nexus/core/prompts/resume_extraction.py`, `src/nexus/core/resume_extractor.py`, `src/nexus/core/schemas/resume.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py` |
| `tests/test_job_parser.py` | `src/nexus/nlp/job_parser.py` |
| `tests/test_job_preferences_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_latest_profile_normalization_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_login_and_session.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `tests/test_login_and_signing.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `tests/test_manual_profile_save_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_ollama_response_validation.py` | `src/nexus/api/routes/resumes.py`, `src/nexus/core/__init__.py`, `src/nexus/core/parser.py`, `src/nexus/core/prompts/resume_extraction.py`, `src/nexus/core/resume_extractor.py`, `src/nexus/core/schemas/resume.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py` |
| `tests/test_parser_and_schema_validation.py` | `src/nexus/api/routes/resumes.py`, `src/nexus/core/__init__.py`, `src/nexus/core/parser.py`, `src/nexus/core/prompts/resume_extraction.py`, `src/nexus/core/resume_extractor.py`, `src/nexus/core/schemas/resume.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py` |
| `tests/test_postgres_profile_upserts.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `tests/test_profile_alias_normalization.py` | `src/nexus/api/routes/resumes.py`, `src/nexus/core/__init__.py`, `src/nexus/core/parser.py`, `src/nexus/core/prompts/resume_extraction.py`, `src/nexus/core/resume_extractor.py`, `src/nexus/core/schemas/resume.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py` |
| `tests/test_profile_owner_access_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_profile_schema_and_sql_sync.py` | `src/nexus/api/routes/resumes.py`, `src/nexus/core/__init__.py`, `src/nexus/core/parser.py`, `src/nexus/core/prompts/resume_extraction.py`, `src/nexus/core/resume_extractor.py`, `src/nexus/core/schemas/resume.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py` |
| `tests/test_profile_validation_and_ai_smart_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_registration_validation.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `tests/test_resume_and_jd_owner_fields.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `tests/test_resume_api_docs.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_resume_delete_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_resume_export_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_resume_gridfs_cleanup.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `tests/test_resume_link_and_ollama_request.py` | `src/nexus/api/routes/resumes.py`, `src/nexus/core/__init__.py`, `src/nexus/core/parser.py`, `src/nexus/core/prompts/resume_extraction.py`, `src/nexus/core/resume_extractor.py`, `src/nexus/core/schemas/resume.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py` |
| `tests/test_resume_parse_and_extract_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_resume_repository_ownership.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `tests/test_resume_retrieval_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_resume_source_recovery.py` | `src/nexus/api/routes/resumes.py`, `src/nexus/core/__init__.py`, `src/nexus/core/parser.py`, `src/nexus/core/prompts/resume_extraction.py`, `src/nexus/core/resume_extractor.py`, `src/nexus/core/schemas/resume.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py` |
| `tests/test_resume_upload_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_rex_rewrite_and_interview_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_route_authentication_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_structured_profile_update_api.py` | `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/api/routes/health.py`, `src/nexus/api/routes/resume/__init__.py`, `src/nexus/api/routes/resume/ai.py`, `src/nexus/api/routes/resume/extract.py`, `src/nexus/api/routes/resume/get.py`, `src/nexus/api/routes/resume/history.py`, `src/nexus/api/routes/resume/parse.py`, `src/nexus/api/routes/resume/upload.py` |
| `tests/test_token_and_owner_scoping.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `tests/test_upload_idempotency.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |
| `tests/test_upload_owner_metadata.py` | `src/nexus/api/__init__.py`, `src/nexus/api/auth.py`, `src/nexus/api/main.py`, `src/nexus/services/__init__.py`, `src/nexus/services/resume_service.py`, `src/nexus/storage/__init__.py`, `src/nexus/storage/jd_repository.py`, `src/nexus/storage/mongodb.py`, `src/nexus/storage/postgres.py`, `src/nexus/storage/resume_repository.py` |

<!-- END GENERATED FILE FLOW MAP -->
