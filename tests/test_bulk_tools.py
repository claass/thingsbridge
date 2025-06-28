"""Unit tests for bulk operation tools."""

import uuid
import pytest
from thingsbridge.tools import (
    complete_todo_bulk,
    create_todo_bulk,
    move_todo_bulk,
    update_todo_bulk,
)

# Helper
IDEMPOTENCY_KEY = uuid.uuid4().hex


def things3_available():
    """Return True if Things 3 automation is available."""
    try:
        from thingsbridge.things3 import client

        return (
            client.executor.check_things_running()
            or client.executor.ensure_things_running().success
        )
    except Exception:
        return False


# ---------------- Validation tests (run even without Things 3) ---------------- #


def test_create_bulk_validation_error():
    resp = create_todo_bulk(idempotency_key="", items=[])
    assert "error" in resp


def test_update_bulk_max_exceeded():
    items = [{"todo_id": "dummy", "title": "x"} for _ in range(1001)]
    resp = update_todo_bulk(idempotency_key=IDEMPOTENCY_KEY, items=items)
    assert resp.get("error")


# ---------------- Live tests (require Things 3) ---------------- #


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_complete_bulk_live():
    # Create two sample todos in bulk
    items = [
        {"title": "Bulk A"},
        {"title": "Bulk B", "notes": "notes"},
    ]
    resp = create_todo_bulk(idempotency_key=IDEMPOTENCY_KEY, items=items)
    assert resp["succeeded"] == 2
    todo_ids = [r.get("id") for r in resp["results"]]
    # Complete them in bulk
    resp2 = complete_todo_bulk(idempotency_key=IDEMPOTENCY_KEY, items=todo_ids)
    assert resp2["succeeded"] == 2


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_bulk_idempotency():
    key = uuid.uuid4().hex
    items = [
        {"title": "Idem A", "client_id": "c1"},
        {"title": "Idem B", "client_id": "c2"},
    ]
    first = create_todo_bulk(idempotency_key=key, items=items)
    second = create_todo_bulk(idempotency_key=key, items=items)
    assert first == second


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_bulk_with_tags():
    key = uuid.uuid4().hex
    items = [
        {"title": "Bulk Tagged A", "tags": ["bulk_tag_a"]},
        {"title": "Bulk Tagged B", "tags": ["bulk_tag_b"]},
    ]
    resp = create_todo_bulk(idempotency_key=key, items=items)
    assert resp["succeeded"] == 2

    from thingsbridge.tools import search_todo

    res_a = search_todo("", tag="bulk_tag_a", limit=5)
    res_b = search_todo("", tag="bulk_tag_b", limit=5)
    assert "Bulk Tagged A" in res_a
    assert "Bulk Tagged B" in res_b
