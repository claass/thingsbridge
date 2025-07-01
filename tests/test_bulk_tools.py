"""Unit tests for bulk operation tools."""

import uuid
import pytest

pytestmark = pytest.mark.integration
from thingsbridge.tools import (
    complete_todo_bulk,
    cancel_todo_bulk,
    delete_todo_bulk,
    create_todo_bulk,
    move_todo_bulk,
    update_todo_bulk,
)
from .test_helpers import create_todo_bulk_tracked, unique_test_name

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


def test_cancel_bulk_validation_error():
    resp = cancel_todo_bulk(idempotency_key="", items="notalist")
    assert "error" in resp


def test_delete_bulk_validation_error():
    resp = delete_todo_bulk(idempotency_key="", items=[])
    assert "error" in resp


# ---------------- Live tests (require Things 3) ---------------- #


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_complete_bulk_live():
    # Create two sample todos in bulk
    items = [
        {"title": unique_test_name("Bulk A")},
        {"title": unique_test_name("Bulk B"), "notes": "notes"},
    ]
    resp = create_todo_bulk_tracked(items=items)
    assert resp["succeeded"] == 2
    todo_ids = [r.get("id") for r in resp["results"]]
    # Complete them in bulk
    resp2 = complete_todo_bulk(idempotency_key=IDEMPOTENCY_KEY, items=todo_ids)
    assert resp2["succeeded"] == 2


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_bulk_idempotency():
    key = uuid.uuid4().hex
    items = [
        {"title": unique_test_name("Idem A"), "client_id": "c1"},
        {"title": unique_test_name("Idem B"), "client_id": "c2"},
    ]
    first = create_todo_bulk_tracked(idempotency_key=key, items=items)
    second = create_todo_bulk_tracked(idempotency_key=key, items=items)
    assert first == second


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_bulk_with_tags():
    key = uuid.uuid4().hex
    tag_a = f"bulk_tag_{uuid.uuid4().hex[:6]}"
    tag_b = f"bulk_tag_{uuid.uuid4().hex[:6]}"
    items = [
        {"title": unique_test_name("Bulk Tagged A"), "tags": [tag_a]},
        {"title": unique_test_name("Bulk Tagged B"), "tags": [tag_b]},
    ]
    resp = create_todo_bulk_tracked(idempotency_key=key, items=items)
    assert resp["succeeded"] == 2

    from thingsbridge.tools import search_todo

    res_a = search_todo("", tag=tag_a, limit=5)
    res_b = search_todo("", tag=tag_b, limit=5)
    assert len(res_a) > 0  # Should find the tagged todo
    assert len(res_b) > 0  # Should find the tagged todo


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_cancel_bulk_live():
    """Test cancel_todo_bulk with real todos."""
    # Create todos to cancel
    items = [
        {"title": unique_test_name("Cancel Bulk A")},
        {"title": unique_test_name("Cancel Bulk B")},
    ]
    create_resp = create_todo_bulk_tracked(items=items)
    assert create_resp["succeeded"] == 2
    
    # Get the todo IDs
    todo_ids = [r.get("id") for r in create_resp["results"]]
    
    # Cancel them in bulk
    cancel_key = uuid.uuid4().hex
    cancel_resp = cancel_todo_bulk(idempotency_key=cancel_key, items=todo_ids)
    assert cancel_resp["succeeded"] == 2
    assert cancel_resp["failed"] == 0


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_delete_bulk_live():
    """Test delete_todo_bulk with real todos."""
    # Create todos to delete
    items = [
        {"title": unique_test_name("Delete Bulk A")},
        {"title": unique_test_name("Delete Bulk B")},
    ]
    create_resp = create_todo_bulk_tracked(items=items)
    assert create_resp["succeeded"] == 2
    
    # Get the todo IDs
    todo_ids = [r.get("id") for r in create_resp["results"]]
    
    # Delete them in bulk
    delete_key = uuid.uuid4().hex
    delete_resp = delete_todo_bulk(idempotency_key=delete_key, items=todo_ids)
    assert delete_resp["succeeded"] == 2
    assert delete_resp["failed"] == 0


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_cancel_delete_bulk_idempotency():
    """Test that cancel and delete bulk operations are idempotent."""
    # Create todos for testing
    items = [
        {"title": unique_test_name("Idempotent Cancel"), "client_id": f"cancel_idem_{uuid.uuid4().hex[:6]}"},
        {"title": unique_test_name("Idempotent Delete"), "client_id": f"delete_idem_{uuid.uuid4().hex[:6]}"},
    ]
    create_resp = create_todo_bulk_tracked(items=items)
    assert create_resp["succeeded"] == 2
    
    todo_ids = [r.get("id") for r in create_resp["results"]]
    
    # Test cancel idempotency
    cancel_key = uuid.uuid4().hex
    first_cancel = cancel_todo_bulk(idempotency_key=cancel_key, items=[todo_ids[0]])
    second_cancel = cancel_todo_bulk(idempotency_key=cancel_key, items=[todo_ids[0]])
    assert first_cancel == second_cancel
    
    # Test delete idempotency
    delete_key = uuid.uuid4().hex
    first_delete = delete_todo_bulk(idempotency_key=delete_key, items=[todo_ids[1]])
    second_delete = delete_todo_bulk(idempotency_key=delete_key, items=[todo_ids[1]])
    assert first_delete == second_delete
