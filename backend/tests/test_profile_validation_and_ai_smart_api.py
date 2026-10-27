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

def test_structured_profile_edit_rejects_invalid_data(client, monkeypatch):
    update = Mock(return_value=True)
    monkeypatch.setattr(history_route, "update_resume", update)
    monkeypatch.setattr(history_route, "get_resume_details", Mock(return_value={"parsed_text": ""}))

    response = client.put("/resumes/6add939dfffc8e3344105dd8/structured-result", json={"structured_result": {"education": [{"graduation_year": "not a year"}]}})

    assert response.status_code == 422
    update.assert_not_called()

def test_ai_smart_uses_owner_profile_and_does_not_persist_draft(client, monkeypatch):
    source = {"structured_result": {"full_name": "Sample Candidate", "skills": ["Python"]}}
    generated = {"full_name": "Sample Candidate", "professional_summary": "A clearer summary.", "skills": ["Python"]}
    get_record = Mock(return_value=source)
    models = Mock(return_value=["llama3.1:8b", "qwen3.5:9b"])
    writer = Mock(return_value=generated)
    monkeypatch.setattr(ai_resume_route, "get_resume_details", get_record)
    monkeypatch.setattr(ai_resume_route, "available_resume_models", models)
    monkeypatch.setattr(ai_resume_route, "write_resume", writer)

    response = client.post("/resumes/6add939dfffc8e3344105dd8/ai-resume", json={"model": "llama3.1:8b", "target_job_description": "Data Engineer"})

    assert response.status_code == 200
    assert response.json()["structured_result"]["professional_summary"] == "A clearer summary."
    get_record.assert_called_once_with("6add939dfffc8e3344105dd8", TEST_USER["app_id"])
    writer.assert_called_once_with(source["structured_result"], "llama3.1:8b", "Data Engineer")

def test_ai_smart_cannot_access_another_users_resume(client, monkeypatch):
    get_record = Mock(return_value=None)
    writer = Mock()
    monkeypatch.setattr(ai_resume_route, "get_resume_details", get_record)
    monkeypatch.setattr(ai_resume_route, "write_resume", writer)

    response = client.post("/resumes/6add939dfffc8e3344105dd8/ai-resume", json={})

    assert response.status_code == 404
    get_record.assert_called_once_with("6add939dfffc8e3344105dd8", TEST_USER["app_id"])
    writer.assert_not_called()
