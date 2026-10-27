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

def test_job_preferences_upsert_updates_by_app_id(monkeypatch):
    connection = Mock()
    connection.__enter__ = Mock(return_value=connection)
    connection.__exit__ = Mock(return_value=False)
    connection.execute.return_value.fetchone.return_value = {"app_id": UUID(TEST_APP_ID)}
    monkeypatch.setattr(postgres, "_connect", lambda: connection)

    result = postgres.upsert_job_preferences(TEST_APP_ID, {
        "current_ctc": "8 LPA", "preferred_locations": ["Pune"],
    })

    query, values = connection.execute.call_args.args
    assert "ON CONFLICT (app_id) DO UPDATE SET" in query
    assert "updated_at = NOW()" in query
    assert values[-1] == TEST_APP_ID
    assert result == {"app_id": TEST_APP_ID}

def test_candidate_profile_upsert_keeps_one_row_per_app_id(monkeypatch):
    connection = Mock()
    connection.__enter__ = Mock(return_value=connection)
    connection.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(postgres, "_connect", lambda: connection)

    postgres.upsert_candidate_profile(TEST_APP_ID, "mongo-document-id", "resume.pdf", {
        "full_name": "Casey Rivera", "references": ["Available on request"],
        "skills": ["Python"], "experience": [],
    })

    query, values = connection.execute.call_args.args
    assert "INSERT INTO public.candidate_profiles" in query
    assert "ON CONFLICT (app_id) DO UPDATE SET" in query
    assert "references_list = EXCLUDED.references_list" in query
    assert values[0] == TEST_APP_ID
    assert values[1] == "mongo-document-id"
    assert values[9].obj == ["Python"]
