from datetime import datetime, timedelta, timezone
from uuid import UUID
from unittest.mock import Mock

import jwt
import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from psycopg.errors import UniqueViolation

from nexus.api import auth
from nexus.api.main import app
from nexus.storage import mongodb, postgres, resume_repository, jd_repository

TEST_SECRET = "test-secret-key-that-is-at-least-32-bytes-long"
TEST_APP_ID = "0e0b3552-a55d-49e9-97c2-bcc4a311a4c3"
TEST_EMAIL = "casey@example.com"
TEST_PASSWORD = "Correct-Horse-Battery-42!"


@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def database_user(password_hash: str | None = None, *, active: bool = True):
    return {
        "id": 23,
        "app_id": UUID(TEST_APP_ID),
        "full_name": "Casey Rivera",
        "email": TEST_EMAIL,
        "password_hash": password_hash or PasswordHasher().hash(TEST_PASSWORD),
        "is_active": active,
        "created_at": datetime.now(timezone.utc),
    }


def test_registration_normalizes_email_hashes_password_and_returns_generated_app_id(client, monkeypatch):
    monkeypatch.setattr(auth, "JWT_SECRET_KEY", TEST_SECRET)
    created = {}

    def fake_create(full_name, email, password_hash):
        created.update(full_name=full_name, email=email, password_hash=password_hash)
        return {key: value for key, value in database_user(password_hash).items() if key != "password_hash"}

    monkeypatch.setattr(postgres, "create_user", fake_create)
    response = client.post("/auth/register", json={
        "full_name": " Casey   Rivera ",
        "email": "CASEY@Example.com",
        "password": TEST_PASSWORD,
        "app_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    })

    assert response.status_code == 201
    body = response.json()
    assert created["full_name"] == "Casey Rivera"
    assert created["email"] == TEST_EMAIL
    assert created["password_hash"] != TEST_PASSWORD
    assert PasswordHasher().verify(created["password_hash"], TEST_PASSWORD)
    assert body["user"]["app_id"] == TEST_APP_ID
    assert "password_hash" not in str(body)
    assert body["access_token"]


def test_registration_rejects_duplicate_email(client, monkeypatch):
    monkeypatch.setattr(auth, "JWT_SECRET_KEY", TEST_SECRET)
    monkeypatch.setattr(postgres, "create_user", Mock(side_effect=UniqueViolation("duplicate")))

    response = client.post("/auth/register", json={
        "full_name": "Casey Rivera", "email": TEST_EMAIL, "password": TEST_PASSWORD,
    })

    assert response.status_code == 409
    assert response.json()["detail"] == "An account with this email already exists."


def test_registration_rejects_short_password(client, monkeypatch):
    create = Mock()
    monkeypatch.setattr(postgres, "create_user", create)

    response = client.post("/auth/register", json={
        "full_name": "Casey Rivera", "email": TEST_EMAIL, "password": "short",
    })

    assert response.status_code == 422
    create.assert_not_called()


def test_registration_fails_closed_without_a_strong_signing_secret(client, monkeypatch):
    create = Mock()
    monkeypatch.setattr(auth, "JWT_SECRET_KEY", "REPLACE_WITH_AT_LEAST_32_RANDOM_BYTES")
    monkeypatch.setattr(postgres, "create_user", create)

    response = client.post("/auth/register", json={
        "full_name": "Casey Rivera", "email": TEST_EMAIL, "password": TEST_PASSWORD,
    })

    assert response.status_code == 503
    create.assert_not_called()


def test_login_issues_token_and_me_resolves_authoritative_postgres_user(client, monkeypatch):
    monkeypatch.setattr(auth, "JWT_SECRET_KEY", TEST_SECRET)
    row = database_user()
    monkeypatch.setattr(postgres, "get_user_by_email", lambda email: row)
    monkeypatch.setattr(postgres, "get_user_by_app_id", lambda app_id: {
        key: value for key, value in row.items() if key != "password_hash"
    })

    response = client.post("/auth/login", json={"email": TEST_EMAIL.upper(), "password": TEST_PASSWORD})
    assert response.status_code == 200
    auth_result = response.json()
    profile = client.get("/auth/me", headers={"Authorization": f"Bearer {auth_result['access_token']}"})

    assert profile.status_code == 200
    assert profile.json() == {
        "app_id": TEST_APP_ID,
        "full_name": "Casey Rivera",
        "email": TEST_EMAIL,
    }


def test_login_uses_generic_error_for_unknown_email_and_wrong_password(client, monkeypatch):
    monkeypatch.setattr(postgres, "get_user_by_email", lambda email: None)
    unknown = client.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    monkeypatch.setattr(postgres, "get_user_by_email", lambda email: database_user())
    wrong = client.post("/auth/login", json={"email": TEST_EMAIL, "password": "wrong password"})

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json()["detail"] == wrong.json()["detail"] == "Email or password is incorrect."


def test_login_rejects_inactive_user(client, monkeypatch):
    monkeypatch.setattr(postgres, "get_user_by_email", lambda email: database_user(active=False))

    response = client.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})

    assert response.status_code == 403
    assert response.json()["detail"] == "This account is inactive."


@pytest.mark.parametrize("authorization", [None, "Bearer not-a-token", "Basic abc"])
def test_me_rejects_missing_malformed_or_wrong_scheme_tokens(client, authorization):
    headers = {} if authorization is None else {"Authorization": authorization}

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 401
    assert "password_hash" not in response.text


def test_me_rejects_expired_and_invalid_signature_tokens(client, monkeypatch):
    monkeypatch.setattr(auth, "JWT_SECRET_KEY", TEST_SECRET)
    now = datetime.now(timezone.utc)
    expired = jwt.encode({
        "sub": TEST_APP_ID, "iat": now - timedelta(hours=2), "exp": now - timedelta(hours=1),
        "iss": auth.JWT_ISSUER, "aud": auth.JWT_AUDIENCE,
    }, TEST_SECRET, algorithm="HS256")
    forged = jwt.encode({
        "sub": TEST_APP_ID, "iat": now, "exp": now + timedelta(minutes=10),
        "iss": auth.JWT_ISSUER, "aud": auth.JWT_AUDIENCE,
    }, "some-other-secret-that-is-also-long-enough", algorithm="HS256")

    for token in (expired, forged):
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_resume_and_jd_repositories_always_scope_reads_and_updates_to_app_id(monkeypatch):
    resume_collection = Mock()
    jd_collection = Mock()
    monkeypatch.setattr(resume_repository, "resumes", resume_collection)
    monkeypatch.setattr(jd_repository, "job_descriptions", jd_collection)
    document_id = "6add939dfffc8e3344105dd8"

    resume_repository.get_resume(document_id, TEST_APP_ID)
    resume_repository.update_resume(document_id, TEST_APP_ID, {"parsed_text": "private"})
    jd_repository.get_jd(document_id, TEST_APP_ID)
    jd_repository.update_jd(document_id, TEST_APP_ID, {"parsed_text": "private"})

    expected_filter = {"_id": resume_repository.ObjectId(document_id), "app_id": TEST_APP_ID}
    resume_collection.find_one.assert_called_once_with(expected_filter)
    resume_collection.update_one.assert_called_once()
    assert resume_collection.update_one.call_args.args[0] == expected_filter
    jd_collection.find_one.assert_called_once_with(expected_filter)
    jd_collection.update_one.assert_called_once()
    assert jd_collection.update_one.call_args.args[0] == expected_filter


def test_upload_storage_sets_same_app_id_on_resume_and_gridfs_metadata(monkeypatch):
    bucket = Mock()
    bucket.upload_from_stream.return_value = "gridfs-original-id"
    collection = Mock()
    monkeypatch.setattr(mongodb, "file_bucket", bucket)

    document_id = mongodb.save_original_file(
        filename="resume.txt",
        content=b"Private candidate data",
        content_type="text/plain",
        collection=collection,
        app_id=TEST_APP_ID,
    )

    assert collection.insert_one.call_args.args[0]["app_id"] == TEST_APP_ID
    assert bucket.upload_from_stream.call_args.kwargs["metadata"]["app_id"] == TEST_APP_ID
    assert collection.insert_one.call_args.args[0]["original_file_id"] == "gridfs-original-id"
    assert collection.insert_one.call_args.args[0]["_id"] == mongodb.ObjectId(document_id)
