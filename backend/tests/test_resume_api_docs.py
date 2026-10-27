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

def test_openapi_documents_resume_endpoints(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/resumes/upload" in paths
    assert "/resumes/{document_id}/parse" in paths
    assert "/resumes/{document_id}/extract" in paths
    assert "/resumes/{document_id}" in paths
    assert "/resumes/latest" in paths
    assert "/resumes/history" not in paths
    assert "/resumes/{document_id}/profile" in paths

def test_root_serves_resume_workspace(client):
    from nexus.api.main import FRONTEND_DIST

    response = client.get("/")

    assert response.status_code == 200
    if (FRONTEND_DIST / "index.html").is_file():
        assert 'id="root"' in response.text
        assert "NEXPLY" in response.text
    else:
        assert response.json()["status"] == "running"

def test_ui_config_exposes_upload_limits(client):
    response = client.get("/api/config")

    assert response.status_code == 200
    assert response.json() == {
        "max_upload_size_mb": 15,
        "supported_formats": [".pdf", ".docx", ".txt"],
    }
