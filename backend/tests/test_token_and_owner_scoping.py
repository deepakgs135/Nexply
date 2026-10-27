from datetime import datetime, timedelta, timezone

import hashlib

from uuid import UUID

from unittest.mock import Mock

import jwt

import pytest

from argon2 import PasswordHasher

from fastapi.testclient import TestClient

from psycopg.errors import UniqueViolation

from pymongo.errors import DuplicateKeyError

from nexus.api import auth

from nexus.api.main import app

from nexus.storage import mongodb, postgres, resume_repository, jd_repository

from nexus.services import resume_service

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
