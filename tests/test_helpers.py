"""Test helper functions with automatic cleanup tracking."""

import uuid
from .test_cleanup import track_created_todo, track_created_project, track_created_tag
from thingsbridge.tools import (
    create_todo as _create_todo,
    create_project as _create_project,
    create_tag as _create_tag,
    create_todo_bulk as _create_todo_bulk,
)


def create_todo_tracked(*args, **kwargs):
    """Create todo with automatic cleanup tracking."""
    result = _create_todo(*args, **kwargs)
    return track_created_todo(result)


def create_project_tracked(*args, **kwargs):
    """Create project with automatic cleanup tracking."""
    result = _create_project(*args, **kwargs) 
    return track_created_project(result)


def create_tag_tracked(name, *args, **kwargs):
    """Create tag with automatic cleanup tracking."""
    result = _create_tag(name, *args, **kwargs)
    if "🏷️ Created tag" in result:
        track_created_tag(name)
    return result


def create_todo_bulk_tracked(idempotency_key=None, items=None):
    """Create todos in bulk with automatic cleanup tracking."""
    if idempotency_key is None:
        idempotency_key = uuid.uuid4().hex
    
    result = _create_todo_bulk(idempotency_key, items or [])
    
    # Track all successfully created todos
    if isinstance(result, dict) and result.get("results"):
        from .test_cleanup import TestCleanupTracker
        tracker = TestCleanupTracker()
        for item_result in result["results"]:
            if item_result.get("id"):
                tracker.track_todo(item_result["id"])
    
    return result


# Convenience function for generating unique test names
def unique_test_name(prefix="Test"):
    """Generate a unique test name with timestamp."""
    return f"{prefix} {uuid.uuid4().hex[:8]}"