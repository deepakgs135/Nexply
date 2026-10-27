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

def test_registration_fails_closed_without_a_strong_signing_secret(client, monkeypatch):
    create = Mock()
    monkeypatch.setattr(auth, "JWT_SECRET_KEY", "REPLACE_WITH_AT_LEAST_32_RANDOM_BYTES")
    monkeypatch.setattr(postgres, "create_user", create)

    response = client.post("/auth/register", json={
        "full_name": "Casey Rivera", "email": TEST_EMAIL, "password": TEST_PASSWORD,
        "confirm_password": TEST_PASSWORD,
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
