import pytest
from unittest.mock import MagicMock

from thingsbridge.applescript import AppleScriptResult
from thingsbridge.core_tools import create_todo, update_todo, _CREATE_TODO_CACHE
from thingsbridge.search_tools import list_areas
from thingsbridge.things3 import client


def _mock_result(success=True, output="", error=None):
    return AppleScriptResult(success=success, output=output, error=error)


def setup_function(function):
    _CREATE_TODO_CACHE.clear()


def test_create_todo_success(monkeypatch):
    monkeypatch.setattr(client, "ensure_running", lambda: None)
    mock_execute = MagicMock(return_value=_mock_result(True, "123"))
    monkeypatch.setattr(client.executor, "execute", mock_execute)

    resp = create_todo("My Task")

    assert resp == "✅ Created todo 'My Task' with ID: 123"
    mock_execute.assert_called_once()


def test_create_todo_failure(monkeypatch):
    monkeypatch.setattr(client, "ensure_running", lambda: None)
    mock_execute = MagicMock(return_value=_mock_result(False, "", "boom"))
    monkeypatch.setattr(client.executor, "execute", mock_execute)

    resp = create_todo("Fail Task")

    assert "❌ Failed to create todo" in resp
    assert "boom" in resp
    mock_execute.assert_called_once()


def test_update_todo_no_updates(monkeypatch):
    monkeypatch.setattr(client, "ensure_running", lambda: None)
    mock_execute = MagicMock()
    monkeypatch.setattr(client.executor, "execute", mock_execute)

    resp = update_todo("abc")

    assert resp == "❌ No updates specified"
    mock_execute.assert_not_called()


def test_create_todo_idempotent(monkeypatch):
    monkeypatch.setattr(client, "ensure_running", lambda: None)
    mock_execute = MagicMock(return_value=_mock_result(True, "XYZ"))
    monkeypatch.setattr(client.executor, "execute", mock_execute)

    first = create_todo("Cache", client_id="cid")
    second = create_todo("Cache", client_id="cid")

    assert first == "✅ Created todo 'Cache' with ID: XYZ"
    assert second == first
    mock_execute.assert_called_once()


def test_list_areas_success(monkeypatch):
    monkeypatch.setattr(client, "ensure_running", lambda: None)
    mock_areas = [{"name": "Area A", "id": "1"}]
    monkeypatch.setattr("thingsbridge.search_tools.areas_list", lambda: mock_areas)

    resp = list_areas()

    assert resp == mock_areas

