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

def test_parse_endpoint_returns_service_result(client, monkeypatch):
    result = {
        "document_id": "resume-test-id",
        "parsing_status": "completed",
        "character_count": 18,
    }
    parse = Mock(return_value=result)
    monkeypatch.setattr(parse_route, "parse_resume", parse)

    response = client.post("/resumes/resume-test-id/parse")

    assert response.status_code == 200
    assert response.json() == result
    parse.assert_called_once_with("resume-test-id", TEST_USER["app_id"])

def test_extract_endpoint_returns_structured_result(client, monkeypatch):
    result = {
        "document_id": "resume-test-id",
        "llm_status": "completed",
        "structured_result": {"full_name": "Sample Person", "skills": []},
    }
    extract = Mock(return_value=result)
    monkeypatch.setattr(extract_route, "extract_resume", extract)

    response = client.post("/resumes/resume-test-id/extract")

    assert response.status_code == 200
    assert response.json() == result
    extract.assert_called_once_with("resume-test-id", TEST_USER["app_id"])
