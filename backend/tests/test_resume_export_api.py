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

def test_rex_manual_profile_cleans_gridfs_file_when_record_save_fails(client, monkeypatch):
    monkeypatch.setattr(ai_resume_route, "create_resume", Mock(side_effect=RuntimeError("database unavailable")))
    upload = Mock(return_value=ObjectId("6add939dfffc8e3344105dd9"))
    delete = Mock()
    monkeypatch.setattr(ai_resume_route.file_bucket, "upload_from_stream", upload)
    monkeypatch.setattr(ai_resume_route.file_bucket, "delete", delete)

    response = client.post("/resumes/manual-profile", json={"structured_result": {"full_name": "Deepak Kumar"}})

    assert response.status_code == 500
    assert response.json()["detail"] == "Unable to save the manually created resume."
    delete.assert_called_once_with(upload.return_value)

def test_ai_resume_export_returns_docx_for_owned_resume(client, monkeypatch):
    monkeypatch.setattr(ai_resume_route, "get_resume_details", Mock(return_value={"structured_result": {"full_name": "Sample Candidate"}}))
    response = client.post("/resumes/6add939dfffc8e3344105dd8/ai-resume/export", json={"structured_result": {"full_name": "Sample Candidate", "skills": ["Python"]}})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert response.content.startswith(b"PK")

def test_resume_export_returns_docx_without_existing_resume(client):
    response = client.post("/resumes/export", json={"structured_result": {
        "full_name": "Sample Candidate",
        "professional_summary": "<p>Led <strong>platform delivery</strong>.</p>",
        "skills": ["Python"],
    }})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert response.headers["content-disposition"].endswith('filename="Sample-Candidate-resume.docx"')
    assert response.content.startswith(b"PK")
    generated_doc = Document(BytesIO(response.content))
    paragraphs = "\n".join(paragraph.text for paragraph in generated_doc.paragraphs)
    assert "Led platform delivery." in paragraphs
    assert "<strong>" not in paragraphs
