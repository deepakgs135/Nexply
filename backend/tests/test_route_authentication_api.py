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

def test_resume_routes_require_authentication():
    app.dependency_overrides.clear()
    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.get("/resumes/6add939dfffc8e3344105dd8")

    assert response.status_code == 401

@pytest.mark.parametrize("path,method", [
    ("/resumes/upload", "post"),
    ("/resumes/6add939dfffc8e3344105dd8/parse", "post"),
    ("/resumes/6add939dfffc8e3344105dd8/extract", "post"),
])
def test_resume_write_and_processing_routes_require_authentication(path, method):
    app.dependency_overrides.clear()
    unauthenticated_client = TestClient(app)
    kwargs = {"files": {"file": ("resume.txt", b"candidate", "text/plain")}} if path.endswith("upload") else {}

    response = getattr(unauthenticated_client, method)(path, **kwargs)

    assert response.status_code == 401

def test_openapi_exposes_auth_routes(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/auth/register" in paths
    assert "/auth/login" in paths
    assert "/auth/me" in paths
