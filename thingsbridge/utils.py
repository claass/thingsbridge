"""Helper functions and utilities for Things 3 integration."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .things3 import ThingsError, client

logger = logging.getLogger(__name__)


# =============================================================================
# DECORATORS
# =============================================================================

def _handle_tool_errors(operation_name: str):
    """Decorator to handle common tool-level errors and return user-friendly messages."""
    def decorator(func):
        import functools
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error {operation_name}: {e}")
                return f"❌ Failed to {operation_name}: {str(e)}"
        return wrapper
    return decorator


# =============================================================================
# APPLESCRIPT HELPERS
# =============================================================================

def _format_applescript_date(date_str: str) -> str:
    """Convert YYYY-MM-DD date string to AppleScript date format."""
    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        return parsed_date.strftime("%B %d, %Y %H:%M:%S")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")


def _schedule_item(item_id: str, when: str, item_type: str = "to do") -> bool:
    """
    Schedule a todo or project using Things 3 schedule command.
    
    Args:
        item_id: The ID of the item to schedule
        when: When to schedule ("today", "tomorrow", or "YYYY-MM-DD")
        item_type: Type of item ("to do" or "project")
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        when_lower = when.lower()
        
        if when_lower == "today":
            schedule_script = f"""
            tell application "Things3"
                schedule {item_type} id "{item_id}" for (current date)
            end tell
            """
        elif when_lower == "tomorrow":
            schedule_script = f"""
            tell application "Things3"
                schedule {item_type} id "{item_id}" for (current date) + 1 * days
            end tell
            """
        else:
            # Try to parse as specific date
            try:
                applescript_date = _format_applescript_date(when)
                schedule_script = f"""
                tell application "Things3"
                    schedule {item_type} id "{item_id}" for (date "{applescript_date}")
                end tell
                """
            except ValueError:
                logger.warning(f"Invalid date format for when: {when}")
                return False

        schedule_result = client.executor.execute(schedule_script)
        if not schedule_result.success:
            logger.warning(f"Failed to schedule {item_type}: {schedule_result.error}")
            return False
        
        return True
        
    except Exception as e:
        logger.warning(f"Error scheduling {item_type}: {e}")
        return False


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def _validate_required_string(value: str, field_name: str) -> Optional[str]:
    """Validate that a required string field is provided and not empty."""
    if not value or not isinstance(value, str) or not value.strip():
        return f"{field_name} is required and cannot be empty"
    return None


def _validate_optional_string(value: Optional[str], field_name: str) -> Optional[str]:
    """Validate an optional string field."""
    if value is not None and not isinstance(value, str):
        return f"{field_name} must be a string"
    return None


def _validate_date_format(date_str: str, field_name: str) -> Optional[str]:
    """Validate date string format (YYYY-MM-DD)."""
    try:
        _format_applescript_date(date_str)
        return None
    except ValueError:
        return f"Invalid {field_name} format: {date_str}. Expected YYYY-MM-DD"


def _validate_destination_type(dest_type: str) -> Optional[str]:
    """Validate destination type for move operations."""
    valid_types = {"area", "project", "list"}
    if dest_type.lower() not in valid_types:
        return f"Invalid destination type: {dest_type}. Use 'area', 'project', or 'list'"
    return None


def _sanitize_applescript_string(text: str) -> str:
    """Escape quotes and special characters for AppleScript."""
    if not text:
        return ""
    return text.replace('"', '\\"')


def _sanitize_applescript_notes(notes: str) -> str:
    """Escape quotes and exclamation marks for AppleScript notes."""
    if not notes:
        return ""
    return notes.replace('"', '\\"').replace("!", "\\!")


# =============================================================================
# BULK OPERATION HELPERS
# =============================================================================

_MAX_BATCH_ITEMS = 1000


def _validate_batch(items: List[Dict[str, Any]], idempotency_key: str) -> Optional[str]:
    """Common validation for *_bulk tools."""
    if not isinstance(items, list):
        return "`items` must be a list"
    if len(items) == 0:
        return "`items` list cannot be empty"
    if len(items) > _MAX_BATCH_ITEMS:
        return f"Batch exceeds maximum of {_MAX_BATCH_ITEMS} items"
    if not idempotency_key:
        return "`idempotency_key` is required"
    return None


def _build_result(index: int, todo_id: str = None, error: str = None):
    """Build standardized result object for bulk operations."""
    if error:
        return {"index": index, "error": {"msg": error}}
    return {"index": index, "id": todo_id}


def _safe_bulk_operation(operation_func, idx: int, *args, **kwargs):
    """Helper to safely execute bulk operations and return standardized results."""
    try:
        result = operation_func(*args, **kwargs)
        # Parse success from result message
        is_success = not (isinstance(result, str) and result.startswith("❌"))
        if is_success and isinstance(result, str) and "ID:" in result:
            # Extract ID if present
            todo_id = result.split("ID:")[-1].strip().rstrip(")")
            return _build_result(idx, todo_id=todo_id)
        elif is_success:
            return _build_result(idx, todo_id="success")
        else:
            return _build_result(idx, error=result)
    except Exception as e:
        return _build_result(idx, error=str(e))