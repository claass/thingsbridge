"""Search and listing functions for Things 3 integration."""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from .applescript_builder import build_search_script, build_list_script
from .cache import cached_resource
from .resources import areas_list, projects_list
from .things3 import ThingsError, client
from .utils import _format_applescript_date, _sanitize_applescript_string, _handle_tool_errors

logger = logging.getLogger(__name__)


@_handle_tool_errors("search todos")
def search_todo(
    query: str,
    limit: int = 10,
    project: Optional[str] = None,
    area: Optional[str] = None,
    tag: Optional[str] = None,
    status: Optional[str] = None,
    due_start: Optional[str] = None,
    due_end: Optional[str] = None,
    scheduled_start: Optional[str] = None,
    scheduled_end: Optional[str] = None,
) -> str:
    """
    Search for todos and projects in Things 3 with optional date filtering.

    Args:
        query: Search query for title/name
        limit: Maximum number of results to return
        project: Only show items from this project
        area: Only show items from this area
        tag: Only show items with this tag
        status: Only show items with this status (open, completed, canceled)
        due_start: Find items with due date >= this date (YYYY-MM-DD format)
        due_end: Find items with due date <= this date (YYYY-MM-DD format)
        scheduled_start: Find items scheduled >= this date (YYYY-MM-DD format) 
        scheduled_end: Find items scheduled <= this date (YYYY-MM-DD format)

    Examples:
        search_todo("", due_start="2024-12-25", due_end="2024-12-31")  # Due this week
        search_todo("meeting", scheduled_start="2024-12-01")  # Meetings scheduled from Dec 1
        search_todo("", due_end="2024-12-31", status="open")  # Open items due by year end

    Returns:
        Formatted search results
    """
    client.ensure_running()

    safe_query = _sanitize_applescript_string(query)

    # Start with the base collection - area or project takes precedence
    if area:
        safe_area = _sanitize_applescript_string(area)
        base_collection = f'to dos of area "{safe_area}"'
    elif project:
        safe_project = _sanitize_applescript_string(project)
        base_collection = f'to dos of project "{safe_project}"'
    else:
        base_collection = "to dos"

    # Build filtering conditions for the selected collection
    conditions = []
    if query:
        conditions.append(f'name contains "{safe_query}"')
    if tag:
        safe_tag = _sanitize_applescript_string(tag)
        conditions.append(f'tag names contains "{safe_tag}"')
    if status:
        conditions.append(f"status is {status.lower()}")

    # Add date range conditions
    if due_start:
        try:
            conditions.append(f'due date ≥ (date "{_format_applescript_date(due_start)}")')
        except ValueError:
            logger.warning(f"Invalid date format for due_start: {due_start}")

    if due_end:
        try:
            conditions.append(f'due date ≤ (date "{_format_applescript_date(due_end)}")')
        except ValueError:
            logger.warning(f"Invalid date format for due_end: {due_end}")

    if scheduled_start:
        try:
            conditions.append(f'activation date ≥ (date "{_format_applescript_date(scheduled_start)}")')
        except ValueError:
            logger.warning(f"Invalid date format for scheduled_start: {scheduled_start}")

    if scheduled_end:
        try:
            conditions.append(f'activation date ≤ (date "{_format_applescript_date(scheduled_end)}")')
        except ValueError:
            logger.warning(f"Invalid date format for scheduled_end: {scheduled_end}")

    # Combine base collection with filtering conditions
    if conditions:
        condition_str = " and ".join(conditions)
        search_clause = f"{base_collection} whose {condition_str}"
    else:
        search_clause = base_collection

    script = build_search_script(search_clause, limit, safe_query)

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Search failed: {result.error}")

    return result.output


@_handle_tool_errors("search due this week")
def search_due_this_week() -> str:
    """
    Find all tasks due this week (next 7 days).
    
    Returns:
        Formatted list of tasks due this week
    """
    today = date.today()
    week_end = today + timedelta(days=7)
    
    return search_todo(
        query="",
        due_start=today.strftime("%Y-%m-%d"),
        due_end=week_end.strftime("%Y-%m-%d"),
        limit=50
    )


@_handle_tool_errors("search scheduled this week")
def search_scheduled_this_week() -> str:
    """
    Find all tasks scheduled this week (next 7 days).
    
    Returns:
        Formatted list of tasks scheduled this week
    """
    today = date.today()
    week_end = today + timedelta(days=7)
    
    return search_todo(
        query="",
        scheduled_start=today.strftime("%Y-%m-%d"),
        scheduled_end=week_end.strftime("%Y-%m-%d"),
        limit=50
    )


@_handle_tool_errors("search overdue")
def search_overdue() -> str:
    """
    Find all overdue tasks (due date before today).
    
    Returns:
        Formatted list of overdue tasks
    """
    yesterday = date.today() - timedelta(days=1)
    
    return search_todo(
        query="",
        due_end=yesterday.strftime("%Y-%m-%d"),
        status="open",
        limit=50
    )


@_handle_tool_errors("list today tasks")
def list_today_tasks() -> str:
    """
    Get today's scheduled tasks.

    Returns:
        Formatted list of today's tasks
    """
    client.ensure_running()

    script = build_list_script("Today", "Today's Tasks")

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to get today's tasks: {result.error}")

    return result.output


@_handle_tool_errors("list inbox items")
def list_inbox_items() -> str:
    """
    Get items in the inbox.

    Returns:
        Formatted list of inbox items
    """
    client.ensure_running()

    script = build_list_script("Inbox", "Inbox")

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to get inbox items: {result.error}")

    return result.output


@_handle_tool_errors("list areas")
def list_areas() -> List[Dict[str, Any]]:
    """Return available Things areas as JSON objects."""
    return areas_list()


@_handle_tool_errors("list projects")
def list_projects() -> List[Dict[str, Any]]:
    """Return available Things projects as JSON objects."""
    return projects_list()


def _fetch_tags_uncached() -> str:
    """Fetch tags from Things 3 without caching."""
    client.ensure_running()

    script = '''
    tell application "Things3"
        set allTags to tags
        set tagCount to count of allTags
        set resultText to "Available Tags (" & tagCount & " tags):\\n\\n"
        
        repeat with i from 1 to tagCount
            set currentTag to item i of allTags
            set tagName to name of currentTag
            set tagId to id of currentTag
            
            set resultText to resultText & "• " & tagName & " (ID: " & tagId & ")"
            
            -- Check for parent tag
            try
                set parentTag to parent tag of currentTag
                if parentTag is not missing value then
                    set parentName to name of parentTag
                    set resultText to resultText & " [Parent: " & parentName & "]"
                end if
            end try
            
            set resultText to resultText & "\\n"
        end repeat
        
        return resultText
    end tell
    '''

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to get tags: {result.error}")

    return result.output


@cached_resource("list_tags", ttl_seconds=300)  # 5 minutes
@_handle_tool_errors("list tags")
def list_tags() -> str:
    """
    Get all available tags in Things 3 (cached for 5 minutes).

    Returns:
    Formatted list of tags
    """
    logger.debug("Fetching tags list (cache miss or expired)")
    return _fetch_tags_uncached()


@_handle_tool_errors("list anytime tasks")
def list_anytime_tasks() -> str:
    """
    Get items in the Anytime list.

    Returns:
        Formatted list of Anytime items
    """
    client.ensure_running()

    script = build_list_script("Anytime", "Anytime Tasks")

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to get Anytime tasks: {result.error}")

    return result.output


@_handle_tool_errors("list someday tasks")
def list_someday_tasks() -> str:
    """
    Get items in the Someday list.

    Returns:
        Formatted list of Someday items
    """
    client.ensure_running()

    script = build_list_script("Someday", "Someday Tasks")

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to get Someday tasks: {result.error}")

    return result.output


@_handle_tool_errors("list upcoming tasks")
def list_upcoming_tasks() -> str:
    """
    Get items in the Upcoming list.

    Returns:
    Formatted list of Upcoming items
    """
    client.ensure_running()

    script = build_list_script("Upcoming", "Upcoming Tasks")

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to get Upcoming tasks: {result.error}")

    return result.output


@_handle_tool_errors("list logbook items")
def list_logbook_items() -> str:
    """
    Get completed items from the Logbook.

    Returns:
    Formatted list of completed items
    """
    client.ensure_running()

    script = build_list_script("Logbook", "Logbook (Completed Items)")

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to get Logbook items: {result.error}")

    return result.output

