# NEXPLY Project File Index

This is the maintained file-by-file guide to the NEXPLY repository. Each first-party file and local project artifact in the current tree is listed below with its purpose. Update the relevant entry whenever a file is added, renamed, moved, repurposed, or removed.

## Inventory scope and maintenance

- Includes project source, tests, documentation, configuration, lockfiles, the local `.env` filename, and the two root-level local artifacts.
- Excludes generated/dependency trees: `.git`, `.venv`, `venv`, `node_modules`, `.pytest_cache`, `__pycache__`, `dist`, `build`, `.mypy_cache`, and `.ruff_cache`. These contain generated files rather than maintained project source.
- `.env` is intentionally listed by name only. Never copy its contents or secrets into this document.
- After changing the tree, update this index and run `python scripts/verify_file_index.py`. The checker detects missing or stale file entries; review descriptions manually when a file's purpose changes.

## Root configuration, documentation, and local artifacts

| File | Purpose |
|---|---|
| `.env` | Local, ignored runtime configuration for secrets and machine-specific settings. Its values are not documented here. |
| `.env.example` | Safe template showing the environment variables required to configure the API and its dependencies. |
| `requirements.txt` | Python runtime and development dependencies installed into the backend environment. |
| `run.py` | Convenience entry point for starting the FastAPI application from the source tree. |
| `CORE_TEST_REPORT.md` | Recorded results and notes from the backend's core verification pass. |
| `ENDPOINT_TRACKER.md` | Endpoint inventory and implementation/testing status tracker. |
| `PROJECT_FILE_INDEX.md` | This maintained, grouped purpose reference for every in-scope file. |
| `resume_from_mongodb.pdf` | Local PDF artifact used for resume extraction or preview work; not application source. |
| `src.zip` | Local source archive artifact; not used as the live Python package. |
| `docs/AUTHENTICATION_SETUP.md` | Setup guide for PostgreSQL authentication, schema prerequisites, and local auth configuration. |
| `scripts/verify_file_index.py` | Checks that every in-scope file is represented in this index and flags stale entries. |

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
