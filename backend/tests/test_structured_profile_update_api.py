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

def test_structured_profile_edit_updates_existing_owner_record(client, monkeypatch):
    update = Mock(return_value=True)
    monkeypatch.setattr(history_route, "update_resume", update)
    monkeypatch.setattr(history_route, "get_resume_details", Mock(return_value={"parsed_text": ""}))
    sync_profile = Mock()
    monkeypatch.setattr(history_route, "sync_candidate_profile_to_sql", sync_profile)
    profile = {"full_name": "Corrected Name", "websites": ["https://example.com"], "skills": ["Python"], "experience": [{
        "job_title": "Engineer", "location": None, "location_string": "Chennai",
        "responsibilities": [], "responsibilities_and_achievements": ["Built a system", "Improved accuracy"],
    }]}

    response = client.put("/resumes/6add939dfffc8e3344105dd8/structured-result", json={"structured_result": profile})

    assert response.status_code == 200
    assert response.json()["structured_result"]["full_name"] == "Corrected Name"
    experience = response.json()["structured_result"]["experience"][0]
    assert experience["location"] == "Chennai"
    assert experience["description"] == "<ul><li>Built a system</li><li>Improved accuracy</li></ul>"
    assert experience["responsibilities"] == []
    assert "location_string" not in experience
    update.assert_called_once()
    args = update.call_args.args
    assert args[0] == "6add939dfffc8e3344105dd8"
    assert args[1] == TEST_USER["app_id"]
    assert args[2]["structured_result"]["websites"] == ["https://example.com"]
    assert args[2]["structured_result"]["experience"][0]["description"] == experience["description"]
    sync_profile.assert_called_once()
    assert sync_profile.call_args.args[0:3] == (
        "6add939dfffc8e3344105dd8", TEST_USER["app_id"], None,
    )

def test_structured_profile_edit_returns_not_found_for_non_owner(client, monkeypatch):
    update = Mock(return_value=False)
    monkeypatch.setattr(history_route, "update_resume", update)
    monkeypatch.setattr(history_route, "get_resume_details", Mock(return_value={"parsed_text": ""}))

    response = client.put("/resumes/6add939dfffc8e3344105dd8/structured-result", json={"structured_result": {"full_name": "Other"}})

    assert response.status_code == 404
    update.assert_called_once()
    assert update.call_args.args[1] == TEST_USER["app_id"]
