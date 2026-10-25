from unittest.mock import Mock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from nexus.api.main import app
from nexus.api.routes.resume import extract as extract_route
from nexus.api.routes.resume import get as get_route
from nexus.api.routes.resume import parse as parse_route
from nexus.api.routes.resume import upload as upload_route
from nexus.api.routes.health import db as health_db


@pytest.fixture
def client():
    return TestClient(app)


def test_openapi_documents_resume_endpoints(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/resumes/upload" in paths
    assert "/resumes/{document_id}/parse" in paths
    assert "/resumes/{document_id}/extract" in paths
    assert "/resumes/{document_id}" in paths


def test_root_serves_resume_workspace(client):
    from nexus.api.main import FRONTEND_DIST

    response = client.get("/")

    assert response.status_code == 200
    if (FRONTEND_DIST / "index.html").is_file():
        assert 'id="root"' in response.text
        assert "NEXPLY" in response.text
    else:
        assert response.json()["status"] == "running"


def test_ui_config_exposes_upload_limits(client):
    response = client.get("/api/config")

    assert response.status_code == 200
    assert response.json() == {
        "max_upload_size_mb": 15,
        "supported_formats": [".pdf", ".docx", ".txt"],
    }


def test_ui_build_assets_are_served(client):
    from nexus.api.main import FRONTEND_DIST

    assets = list((FRONTEND_DIST / "assets").glob("*.js"))
    if not assets:
        pytest.skip("React assets have not been built in this checkout.")
    response = client.get(f"/assets/{assets[0].name}")

    assert response.status_code == 200
    assert "Candidate intelligence" in response.text or "resume" in response.text.lower()


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


def test_upload_accepts_text_file_and_returns_id(client, monkeypatch):
    save = Mock(return_value="resume-test-id")
    monkeypatch.setattr(upload_route, "save_original_file", save)

    response = client.post(
        "/resumes/upload",
        files={"file": ("sample.txt", b"Sample resume text", "text/plain")},
    )

    assert response.status_code == 201
    assert response.json()["document_id"] == "resume-test-id"
    assert response.json()["parsing_status"] == "pending"
    save.assert_called_once()


def test_upload_rejects_unsupported_file(client):
    response = client.post(
        "/resumes/upload",
        files={"file": ("sample.exe", b"not supported", "application/octet-stream")},
    )

    assert response.status_code == 415


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
    parse.assert_called_once_with("resume-test-id")


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
    extract.assert_called_once_with("resume-test-id")


def test_get_endpoint_returns_resume_without_gridfs_id(client, monkeypatch):
    record = {
        "_id": ObjectId("6add939dfffc8e3344105dd8"),
        "original_file_id": ObjectId("6add939dfffc8e3344105dd9"),
        "original_filename": "sample.txt",
        "parsed_text": "Sample resume text",
    }
    get_resume = Mock(return_value=record.copy())
    monkeypatch.setattr(get_route, "get_resume_details", get_resume)

    response = client.get("/resumes/6add939dfffc8e3344105dd8")

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == "6add939dfffc8e3344105dd8"
    assert "original_file_id" not in body
    assert body["parsed_text"] == "Sample resume text"
