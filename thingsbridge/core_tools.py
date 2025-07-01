"""Core CRUD operations for Things 3 integration."""

import logging
from typing import List, Optional, Dict

from .applescript_builder import (
    build_todo_creation_script,
    build_project_creation_script,
    build_todo_update_script,
    build_move_script,
    build_completion_script,
    build_cancellation_script,
    build_delete_script,
    build_tag_addition_script,
    build_get_name_script,
    build_move_to_list_script,
    build_project_cancellation_script,
    build_tag_creation_script,
    build_project_delete_script,
)
from .cache import invalidate_resource_cache
from .resources import areas_list, projects_list
from .things3 import ThingsError, client
from .utils import _format_applescript_date, _handle_tool_errors, _schedule_item

logger = logging.getLogger(__name__)

# Cache for deduplicating create_todo operations when client_id is provided
_CREATE_TODO_CACHE: Dict[str, str] = {}


@_handle_tool_errors("create todo")
def create_todo(
    title: str,
    notes: str = "",
    when: Optional[str] = None,
    deadline: Optional[str] = None,
    tags: Optional[List[str]] = None,
    list_name: Optional[str] = None,
    client_id: Optional[str] = None,
) -> str:
    """
    Create a new todo in Things 3.

    Args:
        title: The todo title (required)
        notes: Additional notes for the todo
        when: When item becomes available to work on (start date). Options:
            - "today", "tomorrow", "someday", or date "YYYY-MM-DD"
            - Example: If application opens July 1st, use when="2024-07-01"
        deadline: When task must be completed (due date in YYYY-MM-DD format)
            - Example: If application deadline is July 10th, use deadline="2024-07-10"
        tags: List of tag names to apply
        list_name: Name of project or area to add todo to
        client_id: Optional stable identifier for idempotent creation

    Returns:
        Success message with todo ID

    See also: create_todo_bulk
    """
    # Ensure Things 3 is running
    if client_id and client_id in _CREATE_TODO_CACHE:
        cached_id = _CREATE_TODO_CACHE[client_id]
        tag_info = f" with tags: {', '.join(tags)}" if tags else ""
        return f"✅ Created todo '{title}'{tag_info} with ID: {cached_id}"

    client.ensure_running()

    # Escape quotes in strings
    safe_title = title.replace('"', '\\"')
    safe_notes = notes.replace('"', '\\"') if notes else ""

    # Build the AppleScript
    properties = [f'name:"{safe_title}"']

    if safe_notes:
        properties.append(f'notes:"{safe_notes}"')

    # Note: We'll handle scheduling after creation using the 'schedule' command
    # For someday, we'll create in the Someday list instead of scheduling
    someday_list = None
    if when and when.lower() == "someday":
        someday_list = "Someday"

    # Handle due date (deadline when task must be completed)
    if deadline:
        try:
            properties.append(
                f'due date:(date "{_format_applescript_date(deadline)}")'
            )
        except ValueError:
            logger.warning(f"Invalid date format for deadline: {deadline}")

    # Note: We'll handle tags after creation due to AppleScript limitations

    properties_str = ", ".join(properties)

    # Build script with optional list assignment
    target_list = list_name or someday_list
    script = build_todo_creation_script(properties, target_list)

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to create todo: {result.error}")

    todo_id = result.output

    # Handle scheduling after creation using the 'schedule' command
    if when and when.lower() != "someday":
        _schedule_item(todo_id, when, "to do")

    # Add tags after creation if specified
    if tags:
        try:
            for tag in tags:
                safe_tag = tag.replace('"', '\\"')
                tag_script = build_tag_addition_script(todo_id, safe_tag)
                tag_result = client.executor.execute(tag_script)
                if not tag_result.success:
                    logger.warning(f"Failed to add tag '{tag}': {tag_result.error}")
        except Exception as e:
            logger.warning(f"Error adding tags: {e}")

    tag_info = f" with tags: {', '.join(tags)}" if tags else ""
    if client_id:
        _CREATE_TODO_CACHE[client_id] = todo_id
    return f"✅ Created todo '{title}'{tag_info} with ID: {todo_id}"


@_handle_tool_errors("create project")
def create_project(
    title: str,
    notes: str = "",
    when: Optional[str] = None,
    deadline: Optional[str] = None,
    tags: Optional[List[str]] = None,
    area: Optional[str] = None,
) -> str:
    """
    Create a new project in Things 3.

    Args:
        title: The project title (required)
        notes: Additional notes for the project
        when: When project becomes available to work on (start date)
            - "today", "tomorrow", or date "YYYY-MM-DD"
        deadline: When project must be completed (due date in YYYY-MM-DD format)
        tags: List of tag names to apply
        area: Area to add project to

    Returns:
        Success message with project ID
    """
    client.ensure_running()

    safe_title = title.replace('"', '\\"')
    safe_notes = notes.replace('"', '\\"') if notes else ""

    properties = [f'name:"{safe_title}"']

    if safe_notes:
        properties.append(f'notes:"{safe_notes}"')

    # Note: We'll handle scheduling after creation using the 'schedule' command

    if deadline:
        try:
            properties.append(
                f'due date:(date "{_format_applescript_date(deadline)}")'
            )
        except ValueError:
            logger.warning(f"Invalid date format for deadline: {deadline}")

    if tags:
        escaped_tags = [tag.replace('"', '\\"') for tag in tags]
        tag_list = "{" + ", ".join([f'"{tag}"' for tag in escaped_tags]) + "}"
        properties.append(f"tag names:{tag_list}")

    if area:
        safe_area = area.replace('"', '\\"')
        properties.append(f'area:area "{safe_area}"')

    properties_str = ", ".join(properties)

    script = build_project_creation_script(properties)

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to create project: {result.error}")

    project_id = result.output

    # Handle scheduling after creation using the 'schedule' command
    if when and when.lower() != "someday":
        _schedule_item(project_id, when, "project")

    # Invalidate projects cache since we added a new project
    invalidate_resource_cache("projects_list")

    return f"📁 Created project '{title}' with ID: {project_id}"


@_handle_tool_errors("update todo")
def update_todo(
    todo_id: str,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    when: Optional[str] = None,
    deadline: Optional[str] = None,
) -> str:
    """
    Update an existing todo in Things 3. Only specify the fields you want to change.

    Args:
        todo_id: The ID of the todo to update (required). Get this from search_todo or list functions.
        title: New title for the todo. Leave None to keep current title.
        notes: New notes for the todo. Use empty string "" to clear notes, None to keep current.
        when: When item becomes available to work on (start date). Options:
            - "today" - Available to work on today
            - "tomorrow" - Available to work on tomorrow  
            - "someday" - Move to Someday area (no specific start date)
            - "2024-07-01" - Available starting specific date (YYYY-MM-DD format)
            - None - Keep current start date
        deadline: When task must be completed (due date in YYYY-MM-DD format, e.g. "2024-07-10"). None keeps current.

    Examples:
        update_todo("ABC123", title="New Title")  # Only change title
        update_todo("ABC123", when="2024-07-01", deadline="2024-07-10")  # App opens July 1, due July 10
        update_todo("ABC123", when="today")  # Available to work on today
        update_todo("ABC123", notes="")  # Clear notes but keep everything else

    Returns:
        Success message with updated todo name

    See also: update_todo_bulk
    """
    client.ensure_running()

    safe_id = todo_id.replace('"', '\\"')
    updates = []

    if title:
        safe_title = title.replace('"', '\\"')
        updates.append(f'set name of targetToDo to "{safe_title}"')

    if notes is not None:  # Allow empty string to clear notes
        safe_notes = notes.replace('"', '\\"').replace("!", "\\!")
        updates.append(f'set notes of targetToDo to "{safe_notes}"')

    # Note: We'll handle scheduling separately using the 'schedule' command
    schedule_when = None
    move_to_someday = False
    if when:
        when_lower = when.lower()
        if when_lower == "someday":
            # For someday, we'll move to Someday list after update
            move_to_someday = True
        else:
            schedule_when = when  # Save for scheduling after update

    if deadline:
        try:
            updates.append(
                f'set due date of targetToDo to (date "{_format_applescript_date(deadline)}")'
            )
        except ValueError:
            logger.warning(f"Invalid date format for deadline: {deadline}")

    if not updates and not schedule_when and not move_to_someday:
        return "❌ No updates specified"

    # Execute updates if there are any
    todo_name = None
    if updates:
        updates_str = "\n            ".join(updates)

        script = build_todo_update_script(safe_id, updates)

        result = client.executor.execute(script)

        if not result.success:
            raise ThingsError(f"Failed to update todo: {result.error}")

        todo_name = result.output
    else:
        # If no property updates, just get the name for the response
        script = build_get_name_script(safe_id)
        result = client.executor.execute(script)
        if not result.success:
            raise ThingsError(f"Failed to get todo name: {result.error}")
        todo_name = result.output

    # Handle scheduling after update using the 'schedule' command
    if schedule_when:
        _schedule_item(safe_id, schedule_when, "to do")

    # Handle moving to Someday list
    if move_to_someday:
        try:
            move_script = build_move_to_list_script(safe_id, "Someday")
            move_result = client.executor.execute(move_script)
            if not move_result.success:
                logger.warning(f"Failed to move todo to Someday: {move_result.error}")
        except Exception as e:
            logger.warning(f"Error moving todo to Someday: {e}")

    return f"✏️ Updated todo: {todo_name}"


@_handle_tool_errors("move todo")
def move_todo(todo_id: str, destination_type: str, destination_name: str) -> str:
    """
    Move a todo to a different area, project, or list in Things 3.

    Args:
        todo_id: The ID of the todo to move (required)
        destination_type: Type of destination ("area", "project", "list")
        destination_name: Name of the destination area, project, or list

    Returns:
        Success message

    See also: move_todo_bulk
    """
    client.ensure_running()

    safe_id = todo_id.replace('"', '\\"')
    safe_destination = destination_name.replace('"', '\\"')

    # Build AppleScript based on destination type
    script = build_move_script(safe_id, destination_type, safe_destination)
    if script.startswith("❌"):
        return script

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to move todo: {result.error}")

    todo_name = result.output
    return f"📁 Moved todo '{todo_name}' to {destination_type} '{destination_name}'"


@_handle_tool_errors("complete todo")
def complete_todo(todo_id: str) -> str:
    """
    Mark a todo as completed.

    Args:
        todo_id: The ID of the todo to complete

    Returns:
        Success message

    See also: complete_todo_bulk
    """
    # Validate required parameters
    if not todo_id or not isinstance(todo_id, str) or not todo_id.strip():
        return "❌ todo_id is required and cannot be empty"
        
    client.ensure_running()

    safe_id = todo_id.replace('"', '\\"')

    script = build_completion_script(safe_id)

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to complete todo: {result.error}")

    todo_name = result.output
    return f"✅ Completed todo: {todo_name}"


@_handle_tool_errors("cancel todo")
def cancel_todo(todo_id: str) -> str:
    """
    Mark a todo as canceled (distinct from completed).

    Args:
        todo_id: The ID of the todo to cancel

    Returns:
        Success message with todo name

    Raises:
        ThingsError: If the cancel operation fails
    """
    if not todo_id or not isinstance(todo_id, str) or not todo_id.strip():
        return "❌ todo_id is required and cannot be empty"

    client.ensure_running()

    safe_id = todo_id.replace('"', '\\"')
    script = build_cancellation_script(safe_id)
    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to cancel todo: {result.error}")

    todo_name = result.output
    return f"🚫 Canceled todo: {todo_name}"


@_handle_tool_errors("cancel project")
def cancel_project(project_id: str) -> str:
    """
    Mark a project as canceled (distinct from completed).

    Args:
    project_id: The ID of the project to cancel

    Returns:
    Success message
    """
    # Validate required parameters
    if not project_id or not isinstance(project_id, str) or not project_id.strip():
        return "❌ project_id is required and cannot be empty"
    
    client.ensure_running()

    safe_id = project_id.replace('"', '\\"')

    script = build_project_cancellation_script(safe_id)

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to cancel project: {result.error}")

    project_name = result.output
    return f"❌ Canceled project: {project_name}"


@_handle_tool_errors("create tag")
def create_tag(name: str, parent_tag: Optional[str] = None) -> str:
    """
    Create a new tag in Things 3.

    Args:
    name: The tag name (required)
    parent_tag: Optional parent tag name to create a hierarchical relationship

    Returns:
    Success message with tag details
    """
    # Validate required parameters
    if not name or not isinstance(name, str) or not name.strip():
        return "❌ tag name is required and cannot be empty"
    
    client.ensure_running()

    safe_name = name.replace('"', '\\"')

    safe_parent = None
    if parent_tag:
        safe_parent = parent_tag.replace('"', '\\"')

    script = build_tag_creation_script(safe_name, safe_parent)

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to create tag: {result.error}")

    tag_info = result.output
    parent_info = f" under parent '{parent_tag}'" if parent_tag else ""
    
    # Invalidate tags cache since we added a new tag
    invalidate_resource_cache("list_tags")
    
    return f"🏷️ Created tag: {tag_info}{parent_info}"


@_handle_tool_errors("delete todo")
def delete_todo(todo_id: str) -> str:
    """
    Delete a todo (move it to Trash).

    Args:
    todo_id: The ID of the todo to delete

    Returns:
    Success message with todo name

    Raises:
    ThingsError: If the delete operation fails
    """
    if not todo_id or not isinstance(todo_id, str) or not todo_id.strip():
        return "❌ todo_id is required and cannot be empty"

    client.ensure_running()

    safe_id = todo_id.replace('"', '\\"')
    script = build_delete_script(safe_id)
    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to delete todo: {result.error}")

    todo_name = result.output
    return f"🗑️ Deleted todo: {todo_name}"


@_handle_tool_errors("delete project")
def delete_project(project_id: str) -> str:
    """
    Delete a project (move it to Trash).

    Args:
    project_id: The ID of the project to delete

    Returns:
    Success message
    """
    # Validate required parameters
    if not project_id or not isinstance(project_id, str) or not project_id.strip():
        return "❌ project_id is required and cannot be empty"
    
    client.ensure_running()

    safe_id = project_id.replace('"', '\\"')

    script = build_project_delete_script(safe_id)

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to delete project: {result.error}")

    project_name = result.output
    
    # Invalidate projects cache since we deleted a project
    invalidate_resource_cache("projects_list")
    
    return f"🗑️ Deleted project: {project_name}"
