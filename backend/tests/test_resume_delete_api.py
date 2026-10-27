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

def test_resume_export_requires_authentication():
    app.dependency_overrides.clear()
    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.post("/resumes/export", json={"structured_result": {"full_name": "Sample Candidate"}})

    assert response.status_code == 401

def test_resume_delete_removes_authenticated_users_item(client, monkeypatch):
    delete = Mock(return_value=True)
    monkeypatch.setattr(history_route, "delete_resume", delete)

    response = client.delete("/resumes/6add939dfffc8e3344105dd8")

    assert response.status_code == 204
    delete.assert_called_once_with("6add939dfffc8e3344105dd8", TEST_USER["app_id"])

def test_resume_delete_returns_not_found_when_record_is_not_owned(client, monkeypatch):
    delete = Mock(return_value=False)
    monkeypatch.setattr(history_route, "delete_resume", delete)

    response = client.delete("/resumes/6add939dfffc8e3344105dd8")

    assert response.status_code == 404

def test_resume_delete_endpoint_requires_authentication(monkeypatch):
    app.dependency_overrides.clear()
    unauthenticated_client = TestClient(app)
    delete = Mock(return_value=True)
    monkeypatch.setattr(history_route, "delete_resume", delete)

    response = unauthenticated_client.delete("/resumes/6add939dfffc8e3344105dd8")

    assert response.status_code == 401
    delete.assert_not_called()
