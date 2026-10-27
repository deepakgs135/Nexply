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

def test_retried_upload_with_same_key_reuses_existing_record_and_gridfs_file(monkeypatch):
    bucket = Mock()
    collection = Mock()
    content = b"Same upload content"
    request_id = "8f35ea21-47b0-4a91-a9a7-18ca5e6b76d9"
    expected_id = mongodb.ObjectId(hashlib.sha256(f"{TEST_APP_ID}:{request_id}".encode()).digest()[:12])
    collection.find_one.return_value = {"upload_sha256": hashlib.sha256(content).hexdigest()}
    monkeypatch.setattr(mongodb, "file_bucket", bucket)

    result = mongodb.save_original_file(
        filename="resume.txt", content=content, content_type="text/plain",
        app_id=TEST_APP_ID, collection=collection, upload_request_id=request_id,
    )

    assert result == str(expected_id)
    bucket.upload_from_stream.assert_not_called()
    collection.insert_one.assert_not_called()

def test_upload_idempotency_key_cannot_be_reused_for_different_content(monkeypatch):
    collection = Mock()
    collection.find_one.return_value = {"upload_sha256": "different-file-hash"}

    with pytest.raises(ValueError, match="different file"):
        mongodb.save_original_file(
            filename="resume.txt", content=b"new content", content_type="text/plain",
            app_id=TEST_APP_ID, collection=collection,
            upload_request_id="8f35ea21-47b0-4a91-a9a7-18ca5e6b76d9",
        )
