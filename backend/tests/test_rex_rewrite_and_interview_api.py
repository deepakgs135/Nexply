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

def test_rex_rewrites_only_requested_field_from_owner_profile(client, monkeypatch):
    source = {"structured_result": {"full_name": "Sample Candidate", "professional_summary": "Old summary."}}
    get_record = Mock(return_value=source)
    rewrite = Mock(return_value={"model": "llama3.1:8b", "rewritten_text": "Improved factual summary."})
    monkeypatch.setattr(ai_resume_route, "get_resume_details", get_record)
    monkeypatch.setattr(ai_resume_route, "rewrite_resume_text", rewrite)

    response = client.post("/resumes/6add939dfffc8e3344105dd8/rex/rewrite", json={"field_path": ["professional_summary"]})

    assert response.status_code == 200
    assert response.json()["rewritten_text"] == "Improved factual summary."
    get_record.assert_called_once_with("6add939dfffc8e3344105dd8", TEST_USER["app_id"])
    rewrite.assert_called_once_with(source["structured_result"], ["professional_summary"], None, "brief")

def test_rex_manual_profile_interview_returns_dynamic_profile(client, monkeypatch):
    profile = {"full_name": "Deepak Kumar", "experience": [], "education": [], "skills": []}
    interview = Mock(return_value={
        "model": "llama3.1:8b", "assistant_message": "What is your current designation at Tata Technologies?",
        "ready_to_save": True, "structured_result": profile,
    })
    monkeypatch.setattr(ai_resume_route, "interview_resume_profile", interview)

    response = client.post("/resumes/manual-profile/interview", json={
        "messages": [{"role": "user", "content": "I am Deepak Kumar and work at Tata Technologies."}],
    })

    assert response.status_code == 200
    assert "current designation" in response.json()["assistant_message"]
    interview.assert_called_once()
