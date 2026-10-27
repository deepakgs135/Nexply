from datetime import datetime, timedelta, timezone
import hashlib
from uuid import UUID
from unittest.mock import Mock

import jwt
import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from psycopg.errors import UniqueViolation
from pymongo.errors import DuplicateKeyError

from nexus.api import auth
from nexus.api.main import app
from nexus.storage import mongodb, postgres, resume_repository, jd_repository
from nexus.services import resume_service

TEST_SECRET = "test-secret-key-that-is-at-least-32-bytes-long"
TEST_APP_ID = "0e0b3552-a55d-49e9-97c2-bcc4a311a4c3"
TEST_EMAIL = "casey@example.com"
TEST_PASSWORD = "Correct-Horse-Battery-42!"


@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def database_user(password_hash: str | None = None, *, active: bool = True):
    return {
        "id": 23,
        "app_id": UUID(TEST_APP_ID),
        "full_name": "Casey Rivera",
        "email": TEST_EMAIL,
        "password_hash": password_hash or PasswordHasher().hash(TEST_PASSWORD),
        "is_active": active,
        "created_at": datetime.now(timezone.utc),
    }


def test_job_preferences_upsert_updates_by_app_id(monkeypatch):
    connection = Mock()
    connection.__enter__ = Mock(return_value=connection)
    connection.__exit__ = Mock(return_value=False)
    connection.execute.return_value.fetchone.return_value = {"app_id": UUID(TEST_APP_ID)}
    monkeypatch.setattr(postgres, "_connect", lambda: connection)

    result = postgres.upsert_job_preferences(TEST_APP_ID, {
        "current_ctc": "8 LPA", "preferred_locations": ["Pune"],
    })

    query, values = connection.execute.call_args.args
    assert "ON CONFLICT (app_id) DO UPDATE SET" in query
    assert "updated_at = NOW()" in query
    assert values[-1] == TEST_APP_ID
    assert result == {"app_id": TEST_APP_ID}


def test_candidate_profile_upsert_keeps_one_row_per_app_id(monkeypatch):
    connection = Mock()
    connection.__enter__ = Mock(return_value=connection)
    connection.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(postgres, "_connect", lambda: connection)

    postgres.upsert_candidate_profile(TEST_APP_ID, "mongo-document-id", "resume.pdf", {
        "full_name": "Casey Rivera", "references": ["Available on request"],
        "skills": ["Python"], "experience": [],
    })

    query, values = connection.execute.call_args.args
    assert "INSERT INTO public.candidate_profiles" in query
    assert "ON CONFLICT (app_id) DO UPDATE SET" in query
    assert "references_list = EXCLUDED.references_list" in query
    assert values[0] == TEST_APP_ID
    assert values[1] == "mongo-document-id"
    assert values[9].obj == ["Python"]


def test_registration_normalizes_email_hashes_password_and_returns_generated_app_id(client, monkeypatch):
    monkeypatch.setattr(auth, "JWT_SECRET_KEY", TEST_SECRET)
    created = {}

    def fake_create(full_name, email, password_hash):
        created.update(full_name=full_name, email=email, password_hash=password_hash)
        return {key: value for key, value in database_user(password_hash).items() if key != "password_hash"}

    monkeypatch.setattr(postgres, "create_user", fake_create)
    response = client.post("/auth/register", json={
        "full_name": " Casey   Rivera ",
        "email": "CASEY@Example.com",
        "password": TEST_PASSWORD,
        "confirm_password": TEST_PASSWORD,
        "app_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    })

    assert response.status_code == 201
    body = response.json()
    assert created["full_name"] == "Casey Rivera"
    assert created["email"] == TEST_EMAIL
    assert created["password_hash"] != TEST_PASSWORD
    assert PasswordHasher().verify(created["password_hash"], TEST_PASSWORD)
    assert body["user"]["app_id"] == TEST_APP_ID
    assert "password_hash" not in str(body)
    assert body["access_token"]


def test_registration_rejects_duplicate_email(client, monkeypatch):
    monkeypatch.setattr(auth, "JWT_SECRET_KEY", TEST_SECRET)
    monkeypatch.setattr(postgres, "create_user", Mock(side_effect=UniqueViolation("duplicate")))

    response = client.post("/auth/register", json={
        "full_name": "Casey Rivera", "email": TEST_EMAIL, "password": TEST_PASSWORD,
        "confirm_password": TEST_PASSWORD,
    })

    assert response.status_code == 409
    assert response.json()["detail"] == "An account with this email already exists."


def test_registration_rejects_short_password(client, monkeypatch):
    create = Mock()
    monkeypatch.setattr(postgres, "create_user", create)

    response = client.post("/auth/register", json={
        "full_name": "Casey Rivera", "email": TEST_EMAIL, "password": "short",
        "confirm_password": "short",
    })

    assert response.status_code == 422
    create.assert_not_called()


def test_registration_fails_closed_without_a_strong_signing_secret(client, monkeypatch):
    create = Mock()
    monkeypatch.setattr(auth, "JWT_SECRET_KEY", "REPLACE_WITH_AT_LEAST_32_RANDOM_BYTES")
    monkeypatch.setattr(postgres, "create_user", create)

    response = client.post("/auth/register", json={
        "full_name": "Casey Rivera", "email": TEST_EMAIL, "password": TEST_PASSWORD,
        "confirm_password": TEST_PASSWORD,
    })

    assert response.status_code == 503
    create.assert_not_called()


def test_login_issues_token_and_me_resolves_authoritative_postgres_user(client, monkeypatch):
    monkeypatch.setattr(auth, "JWT_SECRET_KEY", TEST_SECRET)
    row = database_user()
    monkeypatch.setattr(postgres, "get_user_by_email", lambda email: row)
    monkeypatch.setattr(postgres, "get_user_by_app_id", lambda app_id: {
        key: value for key, value in row.items() if key != "password_hash"
    })

    response = client.post("/auth/login", json={"email": TEST_EMAIL.upper(), "password": TEST_PASSWORD})
    assert response.status_code == 200
    auth_result = response.json()
    profile = client.get("/auth/me", headers={"Authorization": f"Bearer {auth_result['access_token']}"})

    assert profile.status_code == 200
    assert profile.json() == {
        "app_id": TEST_APP_ID,
        "full_name": "Casey Rivera",
        "email": TEST_EMAIL,
    }


def test_login_uses_generic_error_for_unknown_email_and_wrong_password(client, monkeypatch):
    monkeypatch.setattr(postgres, "get_user_by_email", lambda email: None)
    unknown = client.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    monkeypatch.setattr(postgres, "get_user_by_email", lambda email: database_user())
    wrong = client.post("/auth/login", json={"email": TEST_EMAIL, "password": "wrong password"})

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json()["detail"] == wrong.json()["detail"] == "Email or password is incorrect."


def test_login_rejects_inactive_user(client, monkeypatch):
    monkeypatch.setattr(postgres, "get_user_by_email", lambda email: database_user(active=False))

    response = client.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})

    assert response.status_code == 403
    assert response.json()["detail"] == "This account is inactive."


@pytest.mark.parametrize("authorization", [None, "Bearer not-a-token", "Basic abc"])
def test_me_rejects_missing_malformed_or_wrong_scheme_tokens(client, authorization):
    headers = {} if authorization is None else {"Authorization": authorization}

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 401
    assert "password_hash" not in response.text


def test_me_rejects_expired_and_invalid_signature_tokens(client, monkeypatch):
    monkeypatch.setattr(auth, "JWT_SECRET_KEY", TEST_SECRET)
    now = datetime.now(timezone.utc)
    expired = jwt.encode({
        "sub": TEST_APP_ID, "iat": now - timedelta(hours=2), "exp": now - timedelta(hours=1),
        "iss": auth.JWT_ISSUER, "aud": auth.JWT_AUDIENCE,
    }, TEST_SECRET, algorithm="HS256")
    forged = jwt.encode({
        "sub": TEST_APP_ID, "iat": now, "exp": now + timedelta(minutes=10),
        "iss": auth.JWT_ISSUER, "aud": auth.JWT_AUDIENCE,
    }, "some-other-secret-that-is-also-long-enough", algorithm="HS256")

    for token in (expired, forged):
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_resume_and_jd_repositories_always_scope_reads_and_updates_to_app_id(monkeypatch):
    resume_collection = Mock()
    jd_collection = Mock()
    monkeypatch.setattr(resume_repository, "resumes", resume_collection)
    monkeypatch.setattr(jd_repository, "job_descriptions", jd_collection)
    document_id = "6add939dfffc8e3344105dd8"

    resume_repository.get_resume(document_id, TEST_APP_ID)
    resume_repository.update_resume(document_id, TEST_APP_ID, {"parsed_text": "private"})
    jd_repository.get_jd(document_id, TEST_APP_ID)
    jd_repository.update_jd(document_id, TEST_APP_ID, {"parsed_text": "private"})

    expected_filter = {"_id": resume_repository.ObjectId(document_id), "app_id": TEST_APP_ID}
    resume_collection.find_one.assert_called_once_with(expected_filter)
    resume_collection.update_one.assert_called_once()
    assert resume_collection.update_one.call_args.args[0] == expected_filter
    jd_collection.find_one.assert_called_once_with(expected_filter)
    jd_collection.update_one.assert_called_once()
    assert jd_collection.update_one.call_args.args[0] == expected_filter


def test_resume_history_repository_scopes_list_and_count_to_owner(monkeypatch):
    collection = Mock()
    cursor = Mock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__ = Mock(return_value=iter([{"original_filename": "owned.pdf"}]))
    collection.find.return_value = cursor
    collection.count_documents.return_value = 1
    monkeypatch.setattr(resume_repository, "resumes", collection)

    records = resume_repository.list_resumes(TEST_APP_ID, skip=10, limit=20)
    total = resume_repository.count_resumes(TEST_APP_ID)

    assert records == [{"original_filename": "owned.pdf"}]
    assert total == 1
    assert collection.find.call_args.args[0] == {"app_id": TEST_APP_ID}
    cursor.sort.assert_called_once_with("created_at", -1)
    cursor.skip.assert_called_once_with(10)
    cursor.limit.assert_called_once_with(20)
    collection.count_documents.assert_called_once_with({"app_id": TEST_APP_ID})


def test_resume_repository_delete_is_owner_scoped(monkeypatch):
    collection = Mock()
    collection.delete_one.return_value.deleted_count = 1
    monkeypatch.setattr(resume_repository, "resumes", collection)

    assert resume_repository.delete_resume_record("6add939dfffc8e3344105dd8", TEST_APP_ID)
    collection.delete_one.assert_called_once_with({
        "_id": resume_repository.ObjectId("6add939dfffc8e3344105dd8"),
        "app_id": TEST_APP_ID,
    })


def test_resume_service_deletes_original_and_associated_gridfs_files(monkeypatch):
    document_id = "6add939dfffc8e3344105dd8"
    owner = TEST_APP_ID
    original_id = "original-gridfs-id"
    duplicate_id = "duplicate-gridfs-id"
    bucket = Mock()
    cursor = Mock()
    cursor.__iter__ = Mock(return_value=iter([Mock(_id=duplicate_id)]))
    bucket.find.return_value = cursor
    monkeypatch.setattr(resume_service, "file_bucket", bucket)
    monkeypatch.setattr(resume_service, "get_resume", Mock(return_value={"original_file_id": original_id}))
    delete_record = Mock(return_value=True)
    monkeypatch.setattr(resume_service, "delete_resume_record", delete_record)

    assert resume_service.delete_resume(document_id, owner)

    bucket.find.assert_called_once_with({"metadata.document_id": document_id, "metadata.app_id": owner})
    assert {call.args[0] for call in bucket.delete.call_args_list} == {original_id, duplicate_id}
    delete_record.assert_called_once_with(document_id, owner)


@pytest.mark.parametrize("module,collection_name,create_function", [
    (resume_repository, "resumes", "create_resume"),
    (jd_repository, "job_descriptions", "create_jd"),
])
def test_new_resume_and_jd_documents_take_owner_from_authenticated_identity(
    module, collection_name, create_function, monkeypatch
):
    collection = Mock()
    collection.insert_one.return_value.inserted_id = "new-document-id"
    monkeypatch.setattr(module, collection_name, collection)

    created_id = getattr(module, create_function)(
        {"title": "Example", "app_id": "attacker-controlled-value"},
        TEST_APP_ID,
    )

    assert created_id == "new-document-id"
    stored_record = collection.insert_one.call_args.args[0]
    assert stored_record["app_id"] == TEST_APP_ID


@pytest.mark.parametrize("module,update_function", [
    (resume_repository, "update_resume"),
    (jd_repository, "update_jd"),
])
@pytest.mark.parametrize("protected_field", ["app_id", "_id"])
def test_resume_and_jd_owner_and_primary_key_cannot_be_changed(
    module, update_function, protected_field
):
    with pytest.raises(ValueError, match="identity and ownership fields"):
        getattr(module, update_function)(
            "6add939dfffc8e3344105dd8",
            TEST_APP_ID,
            {protected_field: "another-owner"},
        )


def test_upload_storage_sets_same_app_id_on_resume_and_gridfs_metadata(monkeypatch):
    bucket = Mock()
    bucket.upload_from_stream.return_value = "gridfs-original-id"
    collection = Mock()
    monkeypatch.setattr(mongodb, "file_bucket", bucket)

    document_id = mongodb.save_original_file(
        filename="resume.txt",
        content=b"Private candidate data",
        content_type="text/plain",
        collection=collection,
        app_id=TEST_APP_ID,
    )

    assert collection.insert_one.call_args.args[0]["app_id"] == TEST_APP_ID
    assert bucket.upload_from_stream.call_args.kwargs["metadata"]["app_id"] == TEST_APP_ID
    assert collection.insert_one.call_args.args[0]["original_file_id"] == "gridfs-original-id"
    assert collection.insert_one.call_args.args[0]["_id"] == mongodb.ObjectId(document_id)


def test_retried_upload_with_same_key_reuses_existing_record_and_gridfs_file(monkeypatch):
    bucket = Mock()
    collection = Mock()
    content = b"Same upload content"
    request_id = "8f35ea21-47b0-4a91-a9a7-18ca5e6b76d9"
    expected_id = mongodb.ObjectId(hashlib.sha256(f"{TEST_APP_ID}:{request_id}".encode()).digest()[:12])
    collection.find_one.return_value = {"upload_sha256": hashlib.sha256(content).hexdigest()}
    monkeypatch.setattr(mongodb, "file_bucket", bucket)

    result = mongodb.save_original_file(
        filename="resume.txt", content=content, content_type="text/plain",
        app_id=TEST_APP_ID, collection=collection, upload_request_id=request_id,
    )

    assert result == str(expected_id)
    bucket.upload_from_stream.assert_not_called()
    collection.insert_one.assert_not_called()


def test_upload_idempotency_key_cannot_be_reused_for_different_content(monkeypatch):
    collection = Mock()
    collection.find_one.return_value = {"upload_sha256": "different-file-hash"}

    with pytest.raises(ValueError, match="different file"):
        mongodb.save_original_file(
            filename="resume.txt", content=b"new content", content_type="text/plain",
            app_id=TEST_APP_ID, collection=collection,
            upload_request_id="8f35ea21-47b0-4a91-a9a7-18ca5e6b76d9",
        )


def test_concurrent_upload_retry_cleans_duplicate_gridfs_file(monkeypatch):
    bucket = Mock()
    bucket.upload_from_stream.return_value = "duplicate-gridfs-file"
    collection = Mock()
    content = b"Same upload content"
    collection.find_one.side_effect = [None, {"upload_sha256": hashlib.sha256(content).hexdigest()}]
    collection.insert_one.side_effect = DuplicateKeyError("idempotent record already inserted")
    monkeypatch.setattr(mongodb, "file_bucket", bucket)

    result = mongodb.save_original_file(
        filename="resume.txt", content=content, content_type="text/plain",
        app_id=TEST_APP_ID, collection=collection,
        upload_request_id="8f35ea21-47b0-4a91-a9a7-18ca5e6b76d9",
    )

    bucket.delete.assert_called_once_with("duplicate-gridfs-file")
    assert result == str(mongodb.ObjectId(hashlib.sha256(
        f"{TEST_APP_ID}:8f35ea21-47b0-4a91-a9a7-18ca5e6b76d9".encode()
    ).digest()[:12]))
