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

@pytest.mark.parametrize("module,collection_name,create_function", [
    (resume_repository, "resumes", "create_resume"),
    (jd_repository, "job_descriptions", "create_jd"),
])
def test_new_resume_and_jd_documents_take_owner_from_authenticated_identity(
    module, collection_name, create_function, monkeypatch
):
    collection = Mock()
    collection.insert_one.return_value.inserted_id = "new-document-id"
    monkeypatch.setattr(module, collection_name, collection)

    created_id = getattr(module, create_function)(
        {"title": "Example", "app_id": "attacker-controlled-value"},
        TEST_APP_ID,
    )

    assert created_id == "new-document-id"
    stored_record = collection.insert_one.call_args.args[0]
    assert stored_record["app_id"] == TEST_APP_ID

@pytest.mark.parametrize("module,update_function", [
    (resume_repository, "update_resume"),
    (jd_repository, "update_jd"),
])
@pytest.mark.parametrize("protected_field", ["app_id", "_id"])
def test_resume_and_jd_owner_and_primary_key_cannot_be_changed(
    module, update_function, protected_field
):
    with pytest.raises(ValueError, match="identity and ownership fields"):
        getattr(module, update_function)(
            "6add939dfffc8e3344105dd8",
            TEST_APP_ID,
            {protected_field: "another-owner"},
        )
