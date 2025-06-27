"""Tests for MCP tools."""

import pytest
from thingsbridge.tools import (
    todo_create, project_create, todo_search,
    todo_list_today, todo_list_inbox, todo_complete
)

# Only run these tests if Things 3 is available
def things3_available():
    """Check if Things 3 is available for testing."""
    try:
        from thingsbridge.things3 import client
        return client.executor.check_things_running() or client.executor.ensure_things_running().success
    except:
        return False

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_basic():
    """Test basic todo creation."""
    result = todo_create("Test Todo from MCP", "Test notes")
    assert "✅ Created todo" in result
    assert "Test Todo from MCP" in result
    assert "ID:" in result

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_with_scheduling():
    """Test todo creation with scheduling."""
    result = todo_create("Scheduled Todo", "Due today", when="today")
    assert "✅ Created todo" in result
    assert "Scheduled Todo" in result

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_with_tags():
    """Test todo creation with tags."""
    result = todo_create("Tagged Todo", "Has tags", tags=["test", "mcp"])
    assert "✅ Created todo" in result
    assert "Tagged Todo" in result

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_project():
    """Test project creation."""
    result = project_create("Test Project from MCP", "Project notes")
    assert "📁 Created project" in result
    assert "Test Project from MCP" in result
    assert "ID:" in result

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_things():
    """Test search functionality."""
    result = todo_search("Test")
    assert isinstance(result, str)
    assert "Found" in result
    assert "items matching" in result

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_get_today_tasks():
    """Test getting today's tasks."""
    result = todo_list_today()
    assert isinstance(result, str)
    assert "Today's Tasks" in result
    assert "items)" in result

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_get_inbox_items():
    """Test getting inbox items."""
    result = todo_list_inbox()
    assert isinstance(result, str)
    assert "Inbox" in result
    assert "items)" in result

def test_tools_handle_errors_gracefully():
    """Test that tools handle errors gracefully when Things 3 is not available."""
    if things3_available():
        pytest.skip("Things 3 is available, cannot test error handling")
    
    # These should return error messages, not raise exceptions
    result = todo_create("Test")
    assert "❌" in result or "✅" in result  # Either error or success
    
    result = todo_list_inbox()
    assert isinstance(result, str)  # Should return a string either way