from unittest.mock import Mock

from io import BytesIO

import pytest

from bson import ObjectId

from docx import Document

from fastapi.testclient import TestClient

from nexus.api.main import app

from nexus.api.auth import get_current_user

from nexus.api.routes.resume import extract as extract_route

from nexus.api.routes.resume import history as history_route

from nexus.api.routes.resume import ai as ai_resume_route

from nexus.api.routes.resume import get as get_route

from nexus.api.routes.resume import parse as parse_route

from nexus.api.routes.resume import upload as upload_route

from nexus.api.routes.health import db as health_db

TEST_USER = {
    "id": 7,
    "app_id": "0e0b3552-a55d-49e9-97c2-bcc4a311a4c3",
    "full_name": "Test User",
    "email": "test@example.com",
    "is_active": True,
}

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    return TestClient(app)

@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()

def test_upload_accepts_text_file_and_returns_id(client, monkeypatch):
    save = Mock(return_value="resume-test-id")
    monkeypatch.setattr(upload_route, "save_original_file", save)
    monkeypatch.setattr(upload_route, "retain_latest_resume", Mock(return_value=0))

    response = client.post(
        "/resumes/upload",
        files={"file": ("sample.txt", b"Sample resume text", "text/plain")},
        headers={"Idempotency-Key": "64a195bb-e55c-4b4a-91e0-fcd7623fd010"},
    )

    assert response.status_code == 201
    assert response.json()["document_id"] == "resume-test-id"
    assert response.json()["parsing_status"] == "pending"
    assert save.call_args.kwargs["app_id"] == TEST_USER["app_id"]
    assert save.call_args.kwargs["upload_request_id"] == "64a195bb-e55c-4b4a-91e0-fcd7623fd010"

def test_upload_requires_idempotency_key(client):
    response = client.post(
        "/resumes/upload",
        files={"file": ("sample.txt", b"Sample resume text", "text/plain")},
    )

    assert response.status_code == 422

def test_upload_rejects_unsupported_file(client):
    response = client.post(
        "/resumes/upload",
        files={"file": ("sample.exe", b"not supported", "application/octet-stream")},
        headers={"Idempotency-Key": "de7c49f0-a591-4dcf-8a4d-b4925bdbbf62"},
    )

    assert response.status_code == 415
