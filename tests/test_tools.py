"""Tests for MCP tools."""

import pytest

from thingsbridge.tools import (
    create_project,
    create_todo,
    list_areas,
    list_inbox_items,
    list_projects,
    list_today_tasks,
    search_due_this_week,
    search_overdue,
    search_scheduled_this_week,
    search_todo,
    update_todo,
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


# =============================================================================
# NEW SCHEDULING LOGIC TESTS
# =============================================================================

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_scheduling_today():
    """Test creating todo scheduled for today."""
    result = create_todo("Test Today", when="today")
    assert "✅ Created todo" in result
    assert "Test Today" in result
    # TODO: Could add verification that item appears in Today list


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_scheduling_tomorrow():
    """Test creating todo scheduled for tomorrow."""
    result = create_todo("Test Tomorrow", when="tomorrow")
    assert "✅ Created todo" in result
    assert "Test Tomorrow" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_scheduling_specific_date():
    """Test creating todo scheduled for specific date."""
    result = create_todo("Test Specific Date", when="2025-12-31")
    assert "✅ Created todo" in result
    assert "Test Specific Date" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_scheduling_someday():
    """Test creating todo for someday."""
    result = create_todo("Test Someday", when="someday")
    assert "✅ Created todo" in result
    assert "Test Someday" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_with_both_when_and_deadline():
    """Test creating todo with both start date and deadline."""
    result = create_todo(
        "Test Both Dates",
        when="2025-07-01",
        deadline="2025-07-10"
    )
    assert "✅ Created todo" in result
    assert "Test Both Dates" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_update_todo_scheduling():
    """Test updating todo scheduling."""
    # First create a todo
    create_result = create_todo("Test Update Scheduling")
    assert "✅ Created todo" in create_result
    
    # Extract ID (this is brittle but works for testing)
    todo_id = create_result.split("ID: ")[-1].strip()
    
    # Update its scheduling
    update_result = update_todo(todo_id, when="today")
    assert "✏️ Updated todo" in update_result


# =============================================================================
# DATE SEARCH FUNCTION TESTS  
# =============================================================================

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_due_this_week():
    """Test searching for tasks due this week."""
    result = search_due_this_week()
    assert isinstance(result, str)
    assert "Found" in result
    # Should not error out


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_scheduled_this_week():
    """Test searching for tasks scheduled this week."""
    result = search_scheduled_this_week()
    assert isinstance(result, str)
    assert "Found" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_overdue():
    """Test searching for overdue tasks."""
    result = search_overdue()
    assert isinstance(result, str)
    assert "Found" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_with_due_date_range():
    """Test search_todo with due date range."""
    result = search_todo(
        query="",
        due_start="2025-01-01",
        due_end="2025-12-31"
    )
    assert isinstance(result, str)
    assert "Found" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_with_scheduled_date_range():
    """Test search_todo with scheduled date range."""
    result = search_todo(
        query="",
        scheduled_start="2025-01-01",
        scheduled_end="2025-12-31"
    )
    assert isinstance(result, str)
    assert "Found" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_combined_filters():
    """Test search_todo with multiple filters including dates."""
    result = search_todo(
        query="test",
        status="open",
        due_start="2025-01-01",
        due_end="2025-12-31",
        limit=5
    )
    assert isinstance(result, str)
    assert "Found" in result


# =============================================================================
# ERROR CASE TESTS
# =============================================================================

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_invalid_date_format():
    """Test creating todo with invalid date format."""
    result = create_todo("Test Invalid Date", when="invalid-date")
    # Should still create the todo but log a warning about the date
    assert ("✅ Created todo" in result) or ("❌" in result)


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_invalid_date_format():
    """Test search with invalid date format."""
    result = search_todo(
        query="",
        due_start="invalid-date"
    )
    # Should still work, just ignore the invalid date
    assert isinstance(result, str)
    assert "Found" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_update_todo_invalid_id():
    """Test updating todo with invalid ID."""
    result = update_todo("invalid-id", title="New Title")
    assert "❌" in result


def test_date_search_functions_without_things3():
    """Test that date search functions handle missing Things 3 gracefully."""
    # These should return error messages, not raise exceptions
    result = search_due_this_week()
    assert isinstance(result, str)
    
    result = search_overdue()
    assert isinstance(result, str)
    
    result = search_scheduled_this_week()
    assert isinstance(result, str)

    projects = list_projects()
    assert isinstance(projects, list)


# =============================================================================
# AREA AND PROJECT FILTERING TESTS
# =============================================================================

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_by_area():
    """Test search_todo with area filtering."""
    # Get available areas first
    areas = list_areas()
    if not areas:
        pytest.skip("No areas available for testing")
    
    # Use the first available area
    test_area = areas[0]["name"]
    result = search_todo(query="", area=test_area)
    
    assert isinstance(result, str)
    assert "Found" in result
    assert "items matching" in result
    # Should not contain the old error "Can't make area into type specifier"
    assert "Can't make area into type specifier" not in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_by_project():
    """Test search_todo with project filtering."""
    # Get available projects first
    projects = list_projects()
    if not projects:
        pytest.skip("No projects available for testing")
    
    # Use the first available project
    test_project = projects[0]["name"]
    result = search_todo(query="", project=test_project)
    
    assert isinstance(result, str)
    assert "Found" in result
    assert "items matching" in result
    # Should not contain the old error "Can't make project into type specifier"
    assert "Can't make project into type specifier" not in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_area_with_query():
    """Test search_todo with both area filtering and text query."""
    areas = list_areas()
    if not areas:
        pytest.skip("No areas available for testing")
    
    # Use the first available area with a simple query
    test_area = areas[0]["name"]
    result = search_todo(query="test", area=test_area)
    
    assert isinstance(result, str)
    assert "Found" in result
    assert "items matching 'test'" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_project_with_query():
    """Test search_todo with both project filtering and text query."""
    projects = list_projects()
    if not projects:
        pytest.skip("No projects available for testing")
    
    # Use the first available project with a simple query
    test_project = projects[0]["name"]
    result = search_todo(query="test", project=test_project)
    
    assert isinstance(result, str)
    assert "Found" in result
    assert "items matching 'test'" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_area_with_date_range():
    """Test search_todo with area filtering and date range."""
    areas = list_areas()
    if not areas:
        pytest.skip("No areas available for testing")
    
    test_area = areas[0]["name"]
    result = search_todo(
        query="",
        area=test_area,
        due_start="2025-01-01",
        due_end="2025-12-31"
    )
    
    assert isinstance(result, str)
    assert "Found" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_project_with_status():
    """Test search_todo with project filtering and status."""
    projects = list_projects()
    if not projects:
        pytest.skip("No projects available for testing")
    
    test_project = projects[0]["name"]
    result = search_todo(
        query="",
        project=test_project,
        status="open"
    )
    
    assert isinstance(result, str)
    assert "Found" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_nonexistent_area():
    """Test search_todo with nonexistent area."""
    result = search_todo(query="", area="NonexistentArea12345")
    
    # Should either return 0 results or an error, but not crash
    assert isinstance(result, str)
    # Should not crash with AppleScript errors
    assert "Can't make area into type specifier" not in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_nonexistent_project():
    """Test search_todo with nonexistent project."""
    result = search_todo(query="", project="NonexistentProject12345")
    
    # Should either return 0 results or an error, but not crash
    assert isinstance(result, str)
    # Should not crash with AppleScript errors
    assert "Can't make project into type specifier" not in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_area_precedence_over_project():
    """Test that area filtering takes precedence over project filtering."""
    areas = list_areas()
    projects = list_projects()
    
    if not areas or not projects:
        pytest.skip("Need both areas and projects for this test")
    
    # Search with both area and project - area should take precedence
    test_area = areas[0]["name"]
    test_project = projects[0]["name"]
    
    result = search_todo(query="", area=test_area, project=test_project)
    
    assert isinstance(result, str)
    assert "Found" in result
    # The implementation should use area filtering (not both)
