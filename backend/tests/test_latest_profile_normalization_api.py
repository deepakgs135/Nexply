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

def test_latest_resume_returns_only_current_profile(client, monkeypatch):
    record = {
        "_id": ObjectId("6add939dfffc8e3344105dd8"),
        "original_filename": "resume.pdf",
        "original_size_bytes": 12345,
        "created_at": "2026-10-25T12:00:00Z",
        "parsing_status": "completed",
        "llm_status": "completed",
        "structured_result": {"full_name": "Sample Candidate", "professional_title": "Engineer", "education": [{
            "degree": "B.Tech", "institution": "Sample University", "start_date_string": "10/2021",
            "end_date_string": "05/2025", "location_string": "Coimbatore, India", "honors_or_awards": "CGPA:7.7",
        }], "experience": [{
            "job_title": "Engineer", "location": None, "location_string": "Pune", "start_date": "01/2024", "end_date": "Present",
            "responsibilities": [], "responsibilities_and_achievements": ["Built complete feature"],
        }]},
        "parsed_text": "Engineer\n01/2024 – Present\nPune",
    }
    record["app_id"] = TEST_USER["app_id"]
    record["parsed_text"] = "must not be returned"
    get_latest = Mock(return_value=record.copy())
    monkeypatch.setattr(history_route, "get_latest_resume_for_owner", get_latest)
    save_normalized = Mock(return_value=True)
    monkeypatch.setattr(history_route, "update_resume", save_normalized)
    monkeypatch.setattr(history_route.postgres, "get_candidate_profile_source_document_id", Mock(return_value=None))
    sync_profile = Mock()
    monkeypatch.setattr(history_route, "sync_candidate_profile_to_sql", sync_profile)

    response = client.get("/resumes/latest")

    assert response.status_code == 200
    body = response.json()["resume"]
    assert body["document_id"] == "6add939dfffc8e3344105dd8"
    assert body["structured_result"]["full_name"] == "Sample Candidate"
    assert body["structured_result"]["experience"][0]["location"] == "Pune"
    assert body["structured_result"]["experience"][0]["description"] == "<ul><li>Built complete feature</li></ul>"
    assert body["structured_result"]["experience"][0]["responsibilities"] == []
    education = body["structured_result"]["education"][0]
    assert education["start_date"] == "10/2021"
    assert education["end_date"] == "05/2025"
    assert education["location"] == "Coimbatore, India"
    assert education["cgpa_or_percentage"] == "CGPA:7.7"
    assert "start_date_string" not in education
    assert "app_id" not in body
    assert "parsed_text" not in body
    get_latest.assert_called_once_with(TEST_USER["app_id"])
    sync_profile.assert_called_once_with(
        "6add939dfffc8e3344105dd8", TEST_USER["app_id"], "resume.pdf", body["structured_result"],
    )
    save_normalized.assert_called_once()
