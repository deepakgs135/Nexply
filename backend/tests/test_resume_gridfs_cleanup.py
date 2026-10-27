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

def test_resume_service_deletes_original_and_associated_gridfs_files(monkeypatch):
    document_id = "6add939dfffc8e3344105dd8"
    owner = TEST_APP_ID
    original_id = "original-gridfs-id"
    duplicate_id = "duplicate-gridfs-id"
    bucket = Mock()
    cursor = Mock()
    cursor.__iter__ = Mock(return_value=iter([Mock(_id=duplicate_id)]))
    bucket.find.return_value = cursor
    monkeypatch.setattr(resume_service, "file_bucket", bucket)
    monkeypatch.setattr(resume_service, "get_resume", Mock(return_value={"original_file_id": original_id}))
    delete_record = Mock(return_value=True)
    monkeypatch.setattr(resume_service, "delete_resume_record", delete_record)

    assert resume_service.delete_resume(document_id, owner)

    bucket.find.assert_called_once_with({"metadata.document_id": document_id, "metadata.app_id": owner})
    assert {call.args[0] for call in bucket.delete.call_args_list} == {original_id, duplicate_id}
    delete_record.assert_called_once_with(document_id, owner)
