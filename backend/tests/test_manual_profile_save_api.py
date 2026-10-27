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

def test_manual_profile_saves_owner_scoped_latest_record(client, monkeypatch):
    profile = {"full_name": "Deepak Kumar", "professional_title": "Senior Engineer"}
    create = Mock()
    upload = Mock(return_value=ObjectId("6add939dfffc8e3344105dd9"))
    monkeypatch.setattr(ai_resume_route, "create_resume", create)
    monkeypatch.setattr(ai_resume_route.file_bucket, "upload_from_stream", upload)
    monkeypatch.setattr(ai_resume_route, "retain_latest_resume", Mock(return_value=0))
    sync_profile = Mock()
    monkeypatch.setattr(ai_resume_route, "sync_candidate_profile_to_sql", sync_profile)

    response = client.post("/resumes/manual-profile", json={"structured_result": profile})

    assert response.status_code == 200
    assert response.json()["structured_result"]["full_name"] == "Deepak Kumar"
    saved_record, owner_id = create.call_args.args
    assert saved_record["source"] == "rex_manual_profile"
    assert saved_record["original_filename"] == "Deepak-Kumar-resume.docx"
    assert saved_record["original_content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert saved_record["original_size_bytes"] > 0
    assert saved_record["original_file_id"] == upload.return_value
    assert saved_record["_id"] == ObjectId(response.json()["document_id"])
    assert saved_record["structured_result"]["full_name"] == "Deepak Kumar"
    assert owner_id == TEST_USER["app_id"]
    filename, content, metadata = upload.call_args.args[0], upload.call_args.args[1], upload.call_args.kwargs["metadata"]
    assert filename == "Deepak-Kumar-resume.docx"
    assert content.startswith(b"PK")
    generated_doc = Document(BytesIO(content))
    assert any("Senior Engineer" in paragraph.text for paragraph in generated_doc.paragraphs)
    assert metadata["stage"] == "manual_resume"
    assert metadata["document_id"] == response.json()["document_id"]
    assert metadata["app_id"] == TEST_USER["app_id"]
    sync_profile.assert_called_once_with(
        response.json()["document_id"], TEST_USER["app_id"], filename, response.json()["structured_result"],
    )
