'''Unit tests for bulk operation tools.'''

import uuid
import pytest
from thingsbridge.tools import (
    complete_todo_bulk,
    create_todo_bulk,
    move_todo_bulk,
    update_todo_bulk,
    complete_todo_bulk_auto,
    create_todo_bulk_auto,
    move_todo_bulk_auto,
    update_todo_bulk_auto,
)

# Helper
IDEMPOTENCY_KEY = uuid.uuid4().hex


def things3_available():
    """Return True if Things 3 automation is available."""
    try:
        from thingsbridge.things3 import client
        return client.executor.check_things_running() or client.executor.ensure_things_running().success
    except Exception:
        return False


# ---------------- Validation tests (run even without Things 3) ---------------- #

def test_create_bulk_validation_error():
    resp = create_todo_bulk(idempotency_key="", items=[])
    assert "error" in resp


def test_auto_idempotency_generation():
    """Wrapper should auto supply idempotency key."""
    resp = create_todo_bulk_auto(items=[])
    assert resp.get("error") == "`items` list cannot be empty"
    assert "idempotency_key" not in resp.get("error", "")


def test_update_bulk_max_exceeded():
    items = [
        {"todo_id": "dummy", "title": "x"} for _ in range(1001)
    ]
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
