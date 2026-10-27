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
