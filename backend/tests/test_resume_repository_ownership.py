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

def test_resume_history_repository_scopes_list_and_count_to_owner(monkeypatch):
    collection = Mock()
    cursor = Mock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__ = Mock(return_value=iter([{"original_filename": "owned.pdf"}]))
    collection.find.return_value = cursor
    collection.count_documents.return_value = 1
    monkeypatch.setattr(resume_repository, "resumes", collection)

    records = resume_repository.list_resumes(TEST_APP_ID, skip=10, limit=20)
    total = resume_repository.count_resumes(TEST_APP_ID)

    assert records == [{"original_filename": "owned.pdf"}]
    assert total == 1
    assert collection.find.call_args.args[0] == {"app_id": TEST_APP_ID}
    cursor.sort.assert_called_once_with("created_at", -1)
    cursor.skip.assert_called_once_with(10)
    cursor.limit.assert_called_once_with(20)
    collection.count_documents.assert_called_once_with({"app_id": TEST_APP_ID})

def test_resume_repository_delete_is_owner_scoped(monkeypatch):
    collection = Mock()
    collection.delete_one.return_value.deleted_count = 1
    monkeypatch.setattr(resume_repository, "resumes", collection)

    assert resume_repository.delete_resume_record("6add939dfffc8e3344105dd8", TEST_APP_ID)
    collection.delete_one.assert_called_once_with({
        "_id": resume_repository.ObjectId("6add939dfffc8e3344105dd8"),
        "app_id": TEST_APP_ID,
    })
