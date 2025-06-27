"""Tests for MCP tools."""

import pytest

from thingsbridge.tools import (
    create_project,
    create_todo,
    list_areas,
    list_inbox_items,
    list_projects,
    list_today_tasks,
    search_todo,
)


# Only run these tests if Things 3 is available
def things3_available():
    """Check if Things 3 is available for testing."""
    try:
        from thingsbridge.things3 import client

        return (
            client.executor.check_things_running()
            or client.executor.ensure_things_running().success
        )
    except:
        return False


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_basic():
    """Test basic todo creation."""
    result = create_todo("Test Todo from MCP", "Test notes")
    assert "✅ Created todo" in result
    assert "Test Todo from MCP" in result
    assert "ID:" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_with_scheduling():
    """Test todo creation with scheduling."""
    result = create_todo("Scheduled Todo", "Due today", when="today")
    assert "✅ Created todo" in result
    assert "Scheduled Todo" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_with_tags():
    """Test todo creation with tags."""
    result = create_todo("Tagged Todo", "Has tags", tags=["test", "mcp"])
    assert "✅ Created todo" in result
    assert "Tagged Todo" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_project():
    """Test project creation."""
    result = create_project("Test Project from MCP", "Project notes")
    assert "📁 Created project" in result
    assert "Test Project from MCP" in result
    assert "ID:" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_things():
    """Test search functionality."""
    result = search_todo("Test", tag="test")
    assert isinstance(result, str)
    assert "Found" in result
    assert "items matching" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_get_today_tasks():
    """Test getting today's tasks."""
    result = list_today_tasks()
    assert isinstance(result, str)
    assert "Today's Tasks" in result
    assert "items)" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_get_inbox_items():
    """Test getting inbox items."""
    result = list_inbox_items()
    assert isinstance(result, str)
    assert "Inbox" in result
    assert "items)" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_list_areas_json():
    """Areas wrapper should return JSON list."""
    data = list_areas()
    assert isinstance(data, list)
    if data:
        assert isinstance(data[0], dict)
        assert "name" in data[0]


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_list_projects_json():
    """Projects wrapper should return JSON list."""
    data = list_projects()
    assert isinstance(data, list)
    if data:
        assert isinstance(data[0], dict)
        assert "name" in data[0]


def test_tools_handle_errors_gracefully():
    """Test that tools handle errors gracefully when Things 3 is not available."""
    if things3_available():
        pytest.skip("Things 3 is available, cannot test error handling")

    # These should return error messages, not raise exceptions
    result = create_todo("Test")
    assert "❌" in result or "✅" in result  # Either error or success

    result = list_inbox_items()
    assert isinstance(result, str)  # Should return a string either way

    areas = list_areas()
    assert isinstance(areas, list)

    projects = list_projects()
    assert isinstance(projects, list)
