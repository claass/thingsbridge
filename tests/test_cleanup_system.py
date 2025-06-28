"""Test the cleanup system itself."""

import pytest
from .test_cleanup import TestCleanupTracker, cleanup_test_artifacts
from .test_helpers import create_todo_tracked, unique_test_name


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


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_cleanup_tracking():
    """Test that the cleanup system tracks created items."""
    tracker = TestCleanupTracker()
    initial_stats = tracker.get_cleanup_stats()
    
    # Create a test todo using tracked function
    todo_title = unique_test_name("Cleanup Test")
    result = create_todo_tracked(todo_title)
    
    # Verify it was tracked
    new_stats = tracker.get_cleanup_stats()
    assert new_stats['todos'] > initial_stats['todos']
    
    # Verify the result looks correct
    assert "✅ Created todo" in result
    assert todo_title in result


def test_cleanup_stats():
    """Test that cleanup stats work correctly."""
    tracker = TestCleanupTracker()
    stats = tracker.get_cleanup_stats()
    
    # Should return dict with expected keys
    assert isinstance(stats, dict)
    assert 'todos' in stats
    assert 'projects' in stats
    assert 'tags' in stats
    assert all(isinstance(v, int) for v in stats.values())


def test_unique_test_name():
    """Test that unique_test_name generates unique names."""
    name1 = unique_test_name("Test")
    name2 = unique_test_name("Test")
    
    assert name1 != name2
    assert name1.startswith("Test")
    assert name2.startswith("Test")