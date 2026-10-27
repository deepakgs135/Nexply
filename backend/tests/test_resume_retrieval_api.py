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

def test_get_endpoint_returns_resume_without_gridfs_id(client, monkeypatch):
    record = {
        "_id": ObjectId("6add939dfffc8e3344105dd8"),
        "original_file_id": ObjectId("6add939dfffc8e3344105dd9"),
        "original_filename": "sample.txt",
        "parsed_text": "Sample resume text",
    }
    get_resume = Mock(return_value=record.copy())
    monkeypatch.setattr(get_route, "get_resume_details", get_resume)

    response = client.get("/resumes/6add939dfffc8e3344105dd8")

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "6add939dfffc8e3344105dd8"
    assert "original_file_id" not in body
    assert body["parsed_text"] == "Sample resume text"
    get_resume.assert_called_once_with("6add939dfffc8e3344105dd8", TEST_USER["app_id"])
