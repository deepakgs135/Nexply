# NEXPLY authentication setup

## Local configuration

Add these values to the ignored `backend/.env` file. Use the existing least-privileged PostgreSQL role `nexply_app`; do not use `postgres` or another administrator role.

```dotenv
DATABASE_URL=postgresql://nexply_app:URL_ENCODED_ROLE_PASSWORD@localhost:5432/nexply
JWT_SECRET_KEY=GENERATE_A_RANDOM_SECRET
JWT_ISSUER=nexply-api
JWT_AUDIENCE=nexply-web
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate a high-entropy signing key locally with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Keep that value private and do not commit `.env`. If the PostgreSQL password contains URL-reserved characters, percent-encode it before placing it in `DATABASE_URL`.

The authentication API expects the existing `public.users` table to have the columns and types listed in the project database context. The application does not create, alter, or migrate that table. If you need to verify its current structure, these are read-only checks:

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'users'
ORDER BY ordinal_position;

SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.users'::regclass;

SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public' AND tablename = 'users';
```

## Sign-up and sign-in

- `POST /auth/register` accepts `full_name`, `email`, and a password of at least 12 characters. The service normalizes the email, hashes the password with Argon2id, inserts only the hash, and lets PostgreSQL generate `id` and `app_id`.
- `POST /auth/login` verifies the password and account state. Invalid credentials have the same response regardless of whether the email exists.
- `GET /auth/me` accepts `Authorization: Bearer <access_token>`. The token contains only the PostgreSQL-generated `app_id` as its subject and standard issue/expiry/audience claims. The dependency re-reads the active account from PostgreSQL on every request.
- The React app keeps the short-lived bearer token in `sessionStorage`; signing out removes it from the current browser session.

## Data isolation

Resume uploads store the authenticated `app_id` in the MongoDB resume record and the original GridFS metadata. Resume reads, parsing, extraction, and updates filter by both document `_id` and `app_id`. JD repository reads and updates use the same filter. Older MongoDB records without `app_id` remain inaccessible through the authenticated APIs; no migration or reassignment is performed.

## Smoke check

After setting the local values and starting the API, open `/docs`, register a test account, then use the returned bearer token with `/auth/me`. Confirm the returned profile contains no password/hash, upload a test resume, and verify the stored `app_id` is the account's PostgreSQL value. Run the same document id with a different account and confirm GET/parse/extract return 404.
