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

def test_job_preferences_update_is_scoped_to_authenticated_app_id(client, monkeypatch):
    upsert = Mock(return_value={"app_id": TEST_USER["app_id"]})
    monkeypatch.setattr(history_route.postgres, "upsert_job_preferences", upsert)
    preferences = {
        "current_ctc": "8 LPA", "expected_ctc": "12 LPA", "expected_ctc_range": "10-14 LPA",
        "minimum_expected_ctc": "10 LPA", "currency": "INR", "preferred_locations": ["Pune", "Remote"],
    }

    response = client.put("/resumes/preferences", json={"job_preferences": preferences})

    assert response.status_code == 200
    assert response.json()["job_preferences"]["preferred_locations"] == ["Pune", "Remote"]
    upsert.assert_called_once()
    assert upsert.call_args.args[0] == TEST_USER["app_id"]
    assert upsert.call_args.args[1]["minimum_expected_ctc"] == "10 LPA"

def test_job_preferences_load_uses_authenticated_app_id(client, monkeypatch):
    load = Mock(return_value={"current_ctc": "8 LPA", "preferred_locations": ["Pune"]})
    monkeypatch.setattr(history_route.postgres, "get_job_preferences", load)

    response = client.get("/resumes/preferences")

    assert response.status_code == 200
    assert response.json()["configured"] is True
    assert response.json()["job_preferences"]["preferred_locations"] == ["Pune"]
    load.assert_called_once_with(TEST_USER["app_id"])

def test_job_preferences_update_returns_setup_instructions_when_table_missing(client, monkeypatch):
    from psycopg.errors import UndefinedTable

    upsert = Mock(side_effect=UndefinedTable("missing preferences table"))
    monkeypatch.setattr(history_route.postgres, "upsert_job_preferences", upsert)

    response = client.put("/resumes/preferences", json={"job_preferences": {}})

    assert response.status_code == 503
    assert "docs/sql/user_job_preferences.sql" in response.json()["detail"]
    assert upsert.call_args.args[0] == TEST_USER["app_id"]
