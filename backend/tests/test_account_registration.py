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
        "confirm_password": TEST_PASSWORD,
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
