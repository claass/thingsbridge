"""Bulk operation tools for Things 3 integration."""

import logging
import uuid
from typing import Any, Dict, List

from .applescript_builder import (
    build_batch_todo_creation_script,
    build_batch_completion_script,
    build_batch_update_script,
    build_batch_move_script,
)
from .core_tools import complete_todo, create_todo, move_todo, update_todo
from .things3 import ThingsError, client
from .utils import (
    _build_result,
    _safe_bulk_operation,
    _validate_batch,
    _validate_date_format,
    _format_applescript_date,
)

logger = logging.getLogger(__name__)


def create_todo_bulk(
    idempotency_key: str, items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create multiple todos in one batch using native AppleScript batch processing.

    Use this when you need to create many todos at once.

    Args:
        idempotency_key: Client-supplied key for safe retries.
        items: List of {"title": str, "notes": str?, "when": str?, "deadline": str?, "list_name": str?} objects.
    Returns:
        Bulk response dict following guidelines.

    See also: create_todo
    """
    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

    # Validate and prepare items for batch processing
    processed_items = []
    for idx, item in enumerate(items):
        if not item.get("title"):
            return {"error": f"Item {idx}: title is required"}
        
        processed_item = item.copy()
        
        # Validate and format deadline if present
        if "deadline" in item and item["deadline"]:
            date_error = _validate_date_format(item["deadline"], "deadline")
            if date_error:
                return {"error": f"Item {idx}: {date_error}"}
            processed_item["deadline"] = _format_applescript_date(item["deadline"])
        
        processed_items.append(processed_item)

    try:
        client.ensure_running()
        
        # Use native batch AppleScript for significantly better performance
        script = build_batch_todo_creation_script(processed_items)
        result = client.executor.execute(script)
        
        if not result.success:
            raise ThingsError(f"Batch creation failed: {result.error}")
        
        # Parse comma-separated todo IDs from result
        todo_ids = result.output.strip().split(",") if result.output.strip() else []
        
        batch_id = uuid.uuid4().hex
        results = []
        
        for idx, todo_id in enumerate(todo_ids):
            if todo_id.strip():
                results.append(_build_result(idx, todo_id=todo_id.strip()))
            else:
                results.append(_build_result(idx, error="Failed to create todo"))
        
        # Handle scheduling for items that need it (non-someday items)
        for idx, item in enumerate(processed_items):
            when = item.get("when")
            if when and when.lower() != "someday" and idx < len(todo_ids):
                todo_id = todo_ids[idx].strip()
                if todo_id:
                    try:
                        from .utils import _schedule_item
                        _schedule_item(todo_id, when, "to do")
                    except Exception as e:
                        logger.warning(f"Failed to schedule todo {todo_id}: {e}")
        
        succeeded = len([r for r in results if "error" not in r])
        failed = len(results) - succeeded
        
        return {
            "results": results,
            "batch_id": batch_id,
            "processed": len(items),
            "succeeded": succeeded,
            "failed": failed,
        }
        
    except Exception as e:
        logger.error(f"Bulk create operation failed: {e}")
        # Fallback to individual operations if batch fails
        return _fallback_create_todo_bulk(idempotency_key, items)


def complete_todo_bulk(idempotency_key: str, items: List[str]) -> Dict[str, Any]:
    """Complete multiple todos in one batch using native AppleScript batch processing.

    See also: complete_todo
    """
    if not isinstance(items, list):
        return {"error": "items must be list of todo IDs"}
    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

    # Validate todo IDs
    for idx, todo_id in enumerate(items):
        if not todo_id or not isinstance(todo_id, str) or not todo_id.strip():
            return {"error": f"Item {idx}: todo_id is required and cannot be empty"}

    try:
        client.ensure_running()
        
        # Use native batch AppleScript for significantly better performance
        script = build_batch_completion_script(items)
        result = client.executor.execute(script)
        
        if not result.success:
            raise ThingsError(f"Batch completion failed: {result.error}")
        
        # Parse pipe-separated todo names from result
        todo_names = result.output.strip().split("|") if result.output.strip() else []
        
        batch_id = uuid.uuid4().hex
        results = []
        
        for idx, todo_name in enumerate(todo_names):
            if idx < len(items):
                todo_id = items[idx]
                if todo_name.strip():
                    results.append(_build_result(idx, todo_id=todo_id))
                else:
                    results.append(_build_result(idx, error="Failed to complete todo"))
        
        # Handle case where we have fewer results than items
        while len(results) < len(items):
            results.append(_build_result(len(results), error="Failed to complete todo"))
        
        succeeded = len([r for r in results if "error" not in r])
        failed = len(results) - succeeded
        
        return {
            "results": results,
            "batch_id": batch_id,
            "processed": len(items),
            "succeeded": succeeded,
            "failed": failed,
        }
        
    except Exception as e:
        logger.error(f"Bulk complete operation failed: {e}")
        # Fallback to individual operations if batch fails
        return _fallback_complete_todo_bulk(idempotency_key, items)


def move_todo_bulk(idempotency_key: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Move multiple todos in one call.

    Each item: {"todo_id": str, "destination_type": "area|project|list", "destination_name": str}

    See also: move_todo
    """
    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

    batch_id = uuid.uuid4().hex
    results = []
    succeeded = failed = 0
    for idx, itm in enumerate(items):
        try:
            todo_id = itm["todo_id"]
            dest_type = itm["destination_type"]
            dest_name = itm["destination_name"]
            res = move_todo(todo_id, dest_type, dest_name)
            ok = not res.startswith("❌")
            if ok:
                results.append(_build_result(idx, todo_id=todo_id))
                succeeded += 1
            else:
                results.append(_build_result(idx, error=res))
                failed += 1
        except Exception as e:
            results.append(_build_result(idx, error=str(e)))
            failed += 1
    return {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }


def update_todo_bulk(
    idempotency_key: str, items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Update multiple todos in one batch.

    Each item: {"todo_id": str, "title?": str, "notes?": str, "when?": str, "deadline?": str}

    See also: update_todo
    """
    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

    batch_id = uuid.uuid4().hex
    results = []
    succeeded = failed = 0
    for idx, itm in enumerate(items):
        try:
            todo_id = itm["todo_id"]
            title = itm.get("title")
            notes = itm.get("notes")
            when = itm.get("when")
            deadline = itm.get("deadline")
            res = update_todo(
                todo_id, title or None, notes or None, when or None, deadline or None
            )
            ok = not res.startswith("❌")
            if ok:
                results.append(_build_result(idx, todo_id=todo_id))
                succeeded += 1
            else:
                results.append(_build_result(idx, error=res))
                failed += 1
        except Exception as e:
            results.append(_build_result(idx, error=str(e)))
            failed += 1
    return {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }


# =============================================================================
# FALLBACK FUNCTIONS - Individual operations when batch fails
# =============================================================================

def _fallback_create_todo_bulk(idempotency_key: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback to individual create operations when batch fails."""
    batch_id = uuid.uuid4().hex
    results = []
    succeeded = failed = 0

    for idx, itm in enumerate(items):
        try:
            title = itm.get("title")
            notes = itm.get("notes", "")
            when = itm.get("when")
            deadline = itm.get("deadline")
            tags = itm.get("tags")
            list_name = itm.get("list_name")
            
            res = create_todo(title, notes, when, deadline, tags, list_name)
            # Parse ID from success message: "✅ Created todo 'Title' (ID: ABC)"
            todo_id = res.split("ID:")[-1].strip(") ") if "ID:" in res else None
            results.append(_build_result(idx, todo_id=todo_id))
            succeeded += 1
        except Exception as e:
            results.append(_build_result(idx, error=str(e)))
            failed += 1
    return {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }


def _fallback_complete_todo_bulk(idempotency_key: str, items: List[str]) -> Dict[str, Any]:
    """Fallback to individual complete operations when batch fails."""
    batch_id = uuid.uuid4().hex
    results = []
    succeeded = failed = 0
    for idx, todo_id in enumerate(items):
        try:
            res = complete_todo(todo_id)
            ok = not res.startswith("❌")
            if ok:
                results.append(_build_result(idx, todo_id=todo_id))
                succeeded += 1
            else:
                results.append(_build_result(idx, error=res))
                failed += 1
        except Exception as e:
            results.append(_build_result(idx, error=str(e)))
            failed += 1
    return {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }
