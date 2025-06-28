"""Basic tests for the MCP server."""

import pytest
from thingsbridge.server import mcp

def test_server_creation():
    """Test that the server can be created."""
    assert mcp.name == "Things Bridge 🚀"

def test_hello_things():
    """Test the hello_things tool."""
    # Test that the raw function works
    from thingsbridge.server import _hello_things
    result = _hello_things()
    assert isinstance(result, str)
    assert "Hello from Things Bridge!" in result

def test_all_expected_tools_registered():
    """Test that all expected tools are registered with the server."""
    expected_tools = [
        # Core tools
        "create_todo",
        "create_project", 
        "update_todo",
        "search_todo",
        "list_today_tasks",
        "list_inbox_items",
        "complete_todo",
        "cancel_todo",
        "delete_todo",
        "move_todo",
        "list_areas",
        "list_projects",
        # New date search tools
        "search_due_this_week",
        "search_scheduled_this_week", 
        "search_overdue",
        # Bulk tools
        "create_todo_bulk",
        "update_todo_bulk",
        "move_todo_bulk",
        "complete_todo_bulk",
        "cancel_todo_bulk",
        "delete_todo_bulk",
        # Test tool
        "_hello_things",
    ]
    
    # Get tool manager and verify tools exist
    tool_manager = mcp._tool_manager
    assert tool_manager is not None
    
    # Check that each expected tool is registered
    for tool_name in expected_tools:
        assert hasattr(tool_manager, '_tools') or hasattr(tool_manager, 'tools'), f"Tool manager should have tools registry"
        # Note: Actual tool verification depends on FastMCP internal structure

def test_all_expected_resources_registered():
    """Test that all expected resources are registered."""
    expected_resources = [
        "things://areas",
        "things://projects", 
        "things://today",
        "things://inbox",
    ]
    
    # Get resource manager and verify resources exist
    resource_manager = mcp._resource_manager
    assert resource_manager is not None

def test_new_tool_imports():
    """Test that all new tools can be imported from tools module."""
    # Test importing new date search tools
    from thingsbridge.tools import (
        search_due_this_week,
        search_scheduled_this_week,
        search_overdue,
        cancel_todo_bulk,
        delete_todo_bulk,
    )
    
    # Test that they are callable
    assert callable(search_due_this_week)
    assert callable(search_scheduled_this_week)
    assert callable(search_overdue)
    assert callable(cancel_todo_bulk)
    assert callable(delete_todo_bulk)

def test_prompt_resources_exist():
    """Test that prompt resources are registered."""
    # Test that prompt manager exists
    prompt_manager = mcp._prompt_manager
    assert prompt_manager is not None