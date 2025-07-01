"""Bulk operation tools for Things 3 integration."""

import logging
import uuid
from typing import Any, Dict, List

from .applescript_builder import (
    build_batch_completion_script,
    build_batch_move_script,
    build_batch_cancellation_script,
    build_batch_delete_script,
    build_batch_todo_creation_script,
    build_batch_update_script,
    build_tag_addition_script,
    build_move_to_list_script,
)
from .core_tools import (
    complete_todo,
    cancel_todo,
    delete_todo,
    create_todo,
    move_todo,
    update_todo,
)
from .things3 import ThingsError, client
from .cache import create_todo_bulk_cache
from .utils import (
    _build_result,
    _format_applescript_date,
    _validate_batch,
    _validate_date_format,
    _validate_destination_type,
    _handle_tool_errors,
)

logger = logging.getLogger(__name__)

# Persistent cache for create_todo_bulk idempotency
_CREATE_BULK_CACHE = create_todo_bulk_cache
_GENERIC_BULK_CACHE: Dict[str, Dict[str, Any]] = {
    "update": {},
    "move": {},
    "complete": {},
    "cancel": {},
    "delete": {},
}


@_handle_tool_errors("create todo bulk")
def create_todo_bulk(
    idempotency_key: str, items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create multiple todos in one batch using native AppleScript batch processing.

    Use this when you need to create many todos at once.

    Args:
        idempotency_key: Client-supplied key for safe retries.
        items: List of objects with ``title``, optional ``notes``, ``when``,
            ``deadline`` and ``list_name`` fields.
    Returns:
        Bulk response dict following guidelines.

    See also: create_todo
    """
    # Return cached result if this key was already processed
    cached = _CREATE_BULK_CACHE.get(idempotency_key)
    if cached:
        return cached["batch"]

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

    # Apply tags after creation if provided
    for idx, item in enumerate(processed_items):
        tags = item.get("tags")
        if tags and idx < len(todo_ids):
            todo_id = todo_ids[idx].strip()
            if todo_id:
                for tag in tags:
                    safe_tag = tag.replace('"', '\\"')
                    try:
                        tag_script = build_tag_addition_script(todo_id, safe_tag)
                        tag_result = client.executor.execute(tag_script)
                        if not tag_result.success:
                            logger.warning(
                                f"Failed to add tag '{tag}' to {todo_id}: {tag_result.error}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Error adding tag '{tag}' to {todo_id}: {e}"
                        )

    succeeded = len([r for r in results if "error" not in r])
    failed = len(results) - succeeded

    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    # Store results in idempotency cache
    client_map: Dict[str, Dict[str, str]] = {}
    for itm, res in zip(items, results):
        cid = itm.get("client_id")
        if cid:
            client_map[cid] = {"id": res.get("id"), "error": res.get("error")}

    _CREATE_BULK_CACHE.set(idempotency_key, {"batch": batch_result, "clients": client_map})

    return batch_result


@_handle_tool_errors("complete todo bulk")
def complete_todo_bulk(idempotency_key: str, items: List[str]) -> Dict[str, Any]:
    """Complete multiple todos in one batch using native AppleScript batch processing.

    See also: complete_todo
    """
    cached = _GENERIC_BULK_CACHE["complete"].get(idempotency_key)
    if cached:
        return cached

    if not isinstance(items, list):
        return {"error": "items must be list of todo IDs"}
    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

    # Validate todo IDs
    for idx, todo_id in enumerate(items):
        if not todo_id or not isinstance(todo_id, str) or not todo_id.strip():
            return {"error": f"Item {idx}: todo_id is required and cannot be empty"}

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

    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    _GENERIC_BULK_CACHE["complete"][idempotency_key] = batch_result

    return batch_result


@_handle_tool_errors("cancel todo bulk")
def cancel_todo_bulk(idempotency_key: str, items: List[str]) -> Dict[str, Any]:
    """Cancel multiple todos in one batch."""
    cached = _GENERIC_BULK_CACHE["cancel"].get(idempotency_key)
    if cached:
        return cached

    if not isinstance(items, list):
        return {"error": "items must be list of todo IDs"}
    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

    for idx, todo_id in enumerate(items):
        if not todo_id or not isinstance(todo_id, str) or not todo_id.strip():
            return {"error": f"Item {idx}: todo_id is required and cannot be empty"}

    client.ensure_running()

    script = build_batch_cancellation_script(items)
    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Batch cancel failed: {result.error}")

    todo_names = result.output.strip().split("|") if result.output.strip() else []

    batch_id = uuid.uuid4().hex
    results = []

    for idx, todo_name in enumerate(todo_names):
        if idx < len(items):
            todo_id = items[idx]
            if todo_name.strip():
                results.append(_build_result(idx, todo_id=todo_id))
            else:
                results.append(_build_result(idx, error="Failed to cancel todo"))

    while len(results) < len(items):
        results.append(_build_result(len(results), error="Failed to cancel todo"))

    succeeded = len([r for r in results if "error" not in r])
    failed = len(results) - succeeded

    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    _GENERIC_BULK_CACHE["cancel"][idempotency_key] = batch_result

    return batch_result


@_handle_tool_errors("delete todo bulk")
def delete_todo_bulk(idempotency_key: str, items: List[str]) -> Dict[str, Any]:
    """Delete multiple todos in one batch."""
    cached = _GENERIC_BULK_CACHE["delete"].get(idempotency_key)
    if cached:
        return cached

    if not isinstance(items, list):
        return {"error": "items must be list of todo IDs"}
    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

    for idx, todo_id in enumerate(items):
        if not todo_id or not isinstance(todo_id, str) or not todo_id.strip():
            return {"error": f"Item {idx}: todo_id is required and cannot be empty"}

    client.ensure_running()

    script = build_batch_delete_script(items)
    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Batch delete failed: {result.error}")

    todo_names = result.output.strip().split("|") if result.output.strip() else []

    batch_id = uuid.uuid4().hex
    results = []

    for idx, todo_name in enumerate(todo_names):
        if idx < len(items):
            todo_id = items[idx]
            if todo_name.strip():
                results.append(_build_result(idx, todo_id=todo_id))
            else:
                results.append(_build_result(idx, error="Failed to delete todo"))

    while len(results) < len(items):
        results.append(_build_result(len(results), error="Failed to delete todo"))

    succeeded = len([r for r in results if "error" not in r])
    failed = len(results) - succeeded

    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    _GENERIC_BULK_CACHE["delete"][idempotency_key] = batch_result

    return batch_result


@_handle_tool_errors("move todo bulk")
def move_todo_bulk(idempotency_key: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Move multiple todos in one call using native batch execution.

    Each item: {"todo_id": str, "destination_type": "area|project|list",
    "destination_name": str}

    See also: move_todo
    """
    cached = _GENERIC_BULK_CACHE["move"].get(idempotency_key)
    if cached:
        return cached

    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

    # Validate each item and format data for AppleScript
    processed_items = []
    for idx, itm in enumerate(items):
        todo_id = itm.get("todo_id")
        dest_type = itm.get("destination_type")
        dest_name = itm.get("destination_name")
        if not todo_id:
            return {"error": f"Item {idx}: todo_id is required"}
        if not dest_type or not dest_name:
            return {
                "error": (
                    f"Item {idx}: destination_type and destination_name are required"
                )
            }
        dest_error = _validate_destination_type(dest_type)
        if dest_error:
            return {"error": f"Item {idx}: {dest_error}"}
        processed_items.append(
            {
                "todo_id": todo_id,
                "destination_type": dest_type,
                "destination_name": dest_name,
            }
        )

    client.ensure_running()

    script = build_batch_move_script(processed_items)
    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Batch move failed: {result.error}")

    todo_names = result.output.strip().split("|") if result.output.strip() else []

    batch_id = uuid.uuid4().hex
    results = []

    for idx, todo_name in enumerate(todo_names):
        if idx < len(items):
            todo_id = items[idx].get("todo_id")
            if todo_name.strip():
                results.append(_build_result(idx, todo_id=todo_id))
            else:
                results.append(_build_result(idx, error="Failed to move todo"))

    while len(results) < len(items):
        results.append(_build_result(len(results), error="Failed to move todo"))

    succeeded = len([r for r in results if "error" not in r])
    failed = len(results) - succeeded

    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    _GENERIC_BULK_CACHE["move"][idempotency_key] = batch_result

    return batch_result


@_handle_tool_errors("update todo bulk")
def update_todo_bulk(
    idempotency_key: str, items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Update multiple todos in one batch.

    Each item: {"todo_id": str, "title?": str, "notes?": str, "when?": str,
    "deadline?": str}

    See also: update_todo
    """
    cached = _GENERIC_BULK_CACHE["update"].get(idempotency_key)
    if cached:
        return cached

    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

    processed_items = []
    for idx, itm in enumerate(items):
        todo_id = itm.get("todo_id")
        if not todo_id:
            return {"error": f"Item {idx}: todo_id is required"}
        processed_item = {"todo_id": todo_id}
        if "title" in itm and itm["title"]:
            processed_item["title"] = itm["title"]
        if "notes" in itm:
            processed_item["notes"] = itm.get("notes")
        if "deadline" in itm and itm["deadline"]:
            date_error = _validate_date_format(itm["deadline"], "deadline")
            if date_error:
                return {"error": f"Item {idx}: {date_error}"}
            processed_item["deadline"] = _format_applescript_date(itm["deadline"])
        processed_items.append(processed_item)

    client.ensure_running()

    script = build_batch_update_script(processed_items)
    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Batch update failed: {result.error}")

    todo_names = result.output.strip().split("|") if result.output.strip() else []

    batch_id = uuid.uuid4().hex
    results = []

    for idx, todo_name in enumerate(todo_names):
        if idx < len(items):
            todo_id = items[idx].get("todo_id")
            if todo_name.strip():
                results.append(_build_result(idx, todo_id=todo_id))
            else:
                results.append(_build_result(idx, error="Failed to update todo"))

    while len(results) < len(items):
        results.append(_build_result(len(results), error="Failed to update todo"))

    # Handle scheduling and Someday moves separately
    for itm in items:
        when = itm.get("when")
        if when:
            when_lower = when.lower()
            todo_id = itm.get("todo_id")
            if when_lower == "someday":
                try:
                    move_script = build_move_to_list_script(todo_id, "Someday")
                    move_result = client.executor.execute(move_script)
                    if not move_result.success:
                        logger.warning(
                            "Failed to move todo %s to Someday: %s",
                            todo_id,
                            move_result.error,
                        )
                except Exception as e:
                    logger.warning(f"Error moving todo {todo_id} to Someday: {e}")
            else:
                try:
                    from .utils import _schedule_item

                    _schedule_item(todo_id, when, "to do")
                except Exception as e:
                    logger.warning(f"Failed to schedule todo {todo_id}: {e}")

    succeeded = len([r for r in results if "error" not in r])
    failed = len(results) - succeeded

    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    _GENERIC_BULK_CACHE["update"][idempotency_key] = batch_result

    return batch_result


# =============================================================================
# FALLBACK FUNCTIONS - Individual operations when batch fails
# =============================================================================


def _fallback_create_todo_bulk(
    idempotency_key: str, items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Fallback to individual create operations when batch fails."""
    batch_id = uuid.uuid4().hex
    results = []
    succeeded = failed = 0

    client_map: Dict[str, Dict[str, str]] = {}
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
            cid = itm.get("client_id")
            if cid:
                client_map[cid] = {"id": todo_id, "error": None}
            succeeded += 1
        except Exception as e:
            results.append(_build_result(idx, error=str(e)))
            failed += 1
    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    _CREATE_BULK_CACHE.set(idempotency_key, {"batch": batch_result, "clients": client_map})

    return batch_result


def _fallback_complete_todo_bulk(
    idempotency_key: str, items: List[str]
) -> Dict[str, Any]:
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
    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    _GENERIC_BULK_CACHE["complete"][idempotency_key] = batch_result

    return batch_result


def _fallback_move_todo_bulk(
    idempotency_key: str, items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Fallback to individual move operations when batch fails."""
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
    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    _GENERIC_BULK_CACHE["move"][idempotency_key] = batch_result

    return batch_result


def _fallback_update_todo_bulk(
    idempotency_key: str, items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Fallback to individual update operations when batch fails."""
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
    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    _GENERIC_BULK_CACHE["update"][idempotency_key] = batch_result

    return batch_result


def _fallback_cancel_todo_bulk(
    idempotency_key: str, items: List[str]
) -> Dict[str, Any]:
    """Fallback to individual cancel operations when batch fails."""
    batch_id = uuid.uuid4().hex
    results = []
    succeeded = failed = 0
    for idx, todo_id in enumerate(items):
        try:
            res = cancel_todo(todo_id)
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
    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    _GENERIC_BULK_CACHE["cancel"][idempotency_key] = batch_result

    return batch_result


def _fallback_delete_todo_bulk(
    idempotency_key: str, items: List[str]
) -> Dict[str, Any]:
    """Fallback to individual delete operations when batch fails."""
    batch_id = uuid.uuid4().hex
    results = []
    succeeded = failed = 0
    for idx, todo_id in enumerate(items):
        try:
            res = delete_todo(todo_id)
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
    batch_result = {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }

    _GENERIC_BULK_CACHE["delete"][idempotency_key] = batch_result

    return batch_result
