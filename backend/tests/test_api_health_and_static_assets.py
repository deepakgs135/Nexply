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

def test_ui_build_assets_are_served(client):
    from nexus.api.main import FRONTEND_DIST

    assets = list((FRONTEND_DIST / "assets").glob("*.js"))
    if not assets:
        pytest.skip("React assets have not been built in this checkout.")
    response = client.get(f"/assets/{assets[0].name}")

    assert response.status_code == 200
    assert "Profile" in response.text or "resume" in response.text.lower()

def test_ui_favicon_is_served(client):
    from nexus.api.main import FRONTEND_DIST

    if not (FRONTEND_DIST / "nexply.svg").is_file():
        pytest.skip("React assets have not been built in this checkout.")
    response = client.get("/nexply.svg")

    assert response.status_code == 200
    assert "<svg" in response.text

def test_health_checks_mongodb(client, monkeypatch):
    ping = Mock(return_value={"ok": 1.0})
    monkeypatch.setattr(health_db, "command", ping)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "nexply"}
    ping.assert_called_once_with("ping")
