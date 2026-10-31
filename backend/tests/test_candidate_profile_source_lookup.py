from unittest.mock import Mock

from nexus.storage import postgres


APP_ID = "c274522e-3732-4fe9-b1bd-c3f328c1b4d6"


def make_connection(row):
    connection = Mock()
    connection.__enter__ = Mock(return_value=connection)
    connection.__exit__ = Mock(return_value=False)
    connection.execute.return_value.fetchone.return_value = row
    return connection


def test_source_document_lookup_returns_profile_reference(monkeypatch):
    connection = make_connection({"source_document_id": "507f1f77bcf86cd799439011"})
    monkeypatch.setattr(postgres, "_connect", lambda: connection)

    result = postgres.get_candidate_profile_source_document_id(APP_ID)

    assert result == "507f1f77bcf86cd799439011"
    query, params = connection.execute.call_args.args
    assert "FROM public.candidate_profiles" in query
    assert "WHERE app_id = %s::uuid" in query
    assert params == (APP_ID,)


def test_source_document_lookup_returns_none_when_profile_is_missing(monkeypatch):
    connection = make_connection(None)
    monkeypatch.setattr(postgres, "_connect", lambda: connection)

    assert postgres.get_candidate_profile_source_document_id(APP_ID) is None


def test_source_document_lookup_returns_none_when_reference_is_null(monkeypatch):
    connection = make_connection({"source_document_id": None})
    monkeypatch.setattr(postgres, "_connect", lambda: connection)

    assert postgres.get_candidate_profile_source_document_id(APP_ID) is None
