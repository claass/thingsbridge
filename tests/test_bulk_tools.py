'''Unit tests for bulk operation tools.'''

import uuid
import pytest
from thingsbridge.tools import (
    todo_create_bulk,
    todo_complete_bulk,
    todo_move_bulk,
    todo_update_bulk,
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
    resp = todo_create_bulk(idempotency_key="", items=[])
    assert "error" in resp


def test_update_bulk_max_exceeded():
    items = [
        {"todo_id": "dummy", "title": "x"} for _ in range(1001)
    ]
    resp = todo_update_bulk(idempotency_key=IDEMPOTENCY_KEY, items=items)
    assert resp.get("error")


# ---------------- Live tests (require Things 3) ---------------- #

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_complete_bulk_live():
    # Create two sample todos in bulk
    items = [
        {"title": "Bulk A"},
        {"title": "Bulk B", "notes": "notes"},
    ]
    resp = todo_create_bulk(idempotency_key=IDEMPOTENCY_KEY, items=items)
    assert resp["succeeded"] == 2
    todo_ids = [r.get("id") for r in resp["results"]]
    # Complete them in bulk
    resp2 = todo_complete_bulk(idempotency_key=IDEMPOTENCY_KEY, items=todo_ids)
    assert resp2["succeeded"] == 2
