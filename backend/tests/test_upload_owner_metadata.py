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
