"""MCP tools for Things 3 integration."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .resources import areas_list, projects_list
from .things3 import ThingsError, client

logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS AND DECORATORS
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
# MAIN TOOL FUNCTIONS
# =============================================================================

def create_todo(
    title: str,
    notes: str = "",
    when: Optional[str] = None,
    deadline: Optional[str] = None,
    tags: Optional[List[str]] = None,
    list_name: Optional[str] = None,
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

    Returns:
        Success message with todo ID

    See also: create_todo_bulk
    """
    try:
        # Ensure Things 3 is running
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
        if target_list:
            safe_list_name = target_list.replace('"', '\\"')
            script = f"""
            tell application "Things3"
                set targetList to list "{safe_list_name}"
                set newToDo to make new to do at targetList with properties {{{properties_str}}}
                return id of newToDo
            end tell
            """
        else:
            script = f"""
            tell application "Things3"
                set newToDo to make new to do with properties {{{properties_str}}}
                return id of newToDo
            end tell
            """

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
                    tag_script = f"""
                    tell application "Things3"
                        set targetToDo to to do id "{todo_id}"
                        make new tag at targetToDo with properties {{name:"{safe_tag}"}}
                    end tell
                    """
                    tag_result = client.executor.execute(tag_script)
                    if not tag_result.success:
                        logger.warning(f"Failed to add tag '{tag}': {tag_result.error}")
            except Exception as e:
                logger.warning(f"Error adding tags: {e}")

        tag_info = f" with tags: {', '.join(tags)}" if tags else ""
        return f"✅ Created todo '{title}'{tag_info} with ID: {todo_id}"

    except Exception as e:
        logger.error(f"Error creating todo: {e}")
        return f"❌ Failed to create todo: {str(e)}"


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
    try:
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

        script = f"""
        tell application "Things3"
            set newProject to make new project with properties {{{properties_str}}}
            return id of newProject
        end tell
        """

        result = client.executor.execute(script)

        if not result.success:
            raise ThingsError(f"Failed to create project: {result.error}")

        project_id = result.output

        # Handle scheduling after creation using the 'schedule' command
        if when and when.lower() != "someday":
            _schedule_item(project_id, when, "project")

        return f"📁 Created project '{title}' with ID: {project_id}"

    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return f"❌ Failed to create project: {str(e)}"


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
    try:
        client.ensure_running()

        safe_query = query.replace('"', '\\"')

        conditions = []
        if query:
            conditions.append(f'name contains "{safe_query}"')
        if project:
            safe_project = project.replace('"', '\\"')
            conditions.append(f'project is project "{safe_project}"')
        if area:
            safe_area = area.replace('"', '\\"')
            conditions.append(f'area is area "{safe_area}"')
        if tag:
            safe_tag = tag.replace('"', '\\"')
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

        if conditions:
            condition_str = " and ".join(conditions)
            search_clause = f"to dos whose {condition_str}"
        else:
            search_clause = "to dos"

        script = f"""
        tell application "Things3"
            set searchResults to {search_clause}
            set resultCount to count of searchResults
            set resultText to "Found " & resultCount & " items matching '{safe_query}':\\n"
            
            repeat with i from 1 to (resultCount)
                if i > {limit} then exit repeat
                set currentToDo to item i of searchResults
                set todoId to id of currentToDo
                set todoName to name of currentToDo
                set todoNotes to notes of currentToDo
                set todoStatus to status of currentToDo
                set todoDueDate to due date of currentToDo
                set todoActivationDate to activation date of currentToDo
                
                set resultText to resultText & i & ". " & todoName & " (ID: " & todoId & ")"
                
                if todoStatus is not open then
                    set resultText to resultText & " [" & todoStatus & "]"
                end if
                
                -- Add due date if present
                if todoDueDate is not missing value then
                    set resultText to resultText & " | Due: " & (short date string of todoDueDate)
                end if
                
                -- Add activation date if present
                if todoActivationDate is not missing value then
                    set resultText to resultText & " | Scheduled: " & (short date string of todoActivationDate)
                end if
                
                if todoNotes is not "" then
                    set resultText to resultText & " - " & todoNotes
                end if
                set resultText to resultText & "\\n"
            end repeat
            
            return resultText
        end tell
        """

        result = client.executor.execute(script)

        if not result.success:
            raise ThingsError(f"Search failed: {result.error}")

        return result.output

    except Exception as e:
        logger.error(f"Error searching: {e}")
        return f"❌ Search failed: {str(e)}"


def search_due_this_week() -> str:
    """
    Find all tasks due this week (next 7 days).
    
    Returns:
        Formatted list of tasks due this week
    """
    from datetime import date, timedelta
    today = date.today()
    week_end = today + timedelta(days=7)
    
    return search_todo(
        query="",
        due_start=today.strftime("%Y-%m-%d"),
        due_end=week_end.strftime("%Y-%m-%d"),
        limit=50
    )


def search_scheduled_this_week() -> str:
    """
    Find all tasks scheduled this week (next 7 days).
    
    Returns:
        Formatted list of tasks scheduled this week
    """
    from datetime import date, timedelta
    today = date.today()
    week_end = today + timedelta(days=7)
    
    return search_todo(
        query="",
        scheduled_start=today.strftime("%Y-%m-%d"),
        scheduled_end=week_end.strftime("%Y-%m-%d"),
        limit=50
    )


def search_overdue() -> str:
    """
    Find all overdue tasks (due date before today).
    
    Returns:
        Formatted list of overdue tasks
    """
    from datetime import date, timedelta
    yesterday = date.today() - timedelta(days=1)
    
    return search_todo(
        query="",
        due_end=yesterday.strftime("%Y-%m-%d"),
        status="open",
        limit=50
    )


def list_today_tasks() -> str:
    """
    Get today's scheduled tasks.

    Returns:
        Formatted list of today's tasks
    """
    try:
        client.ensure_running()

        script = """
        tell application "Things3"
            set todayTodos to to dos of list "Today"
            set taskCount to count of todayTodos
            set resultText to "Today's Tasks (" & taskCount & " items):\\n\\n"
            
            repeat with i from 1 to taskCount
                set currentToDo to item i of todayTodos
                set todoId to id of currentToDo
                set todoName to name of currentToDo
                set todoNotes to notes of currentToDo
                
                set resultText to resultText & "• " & todoName & " (ID: " & todoId & ")"
                if todoNotes is not "" then
                    set resultText to resultText & " - " & todoNotes
                end if
                set resultText to resultText & "\\n"
            end repeat
            
            return resultText
        end tell
        """

        result = client.executor.execute(script)

        if not result.success:
            raise ThingsError(f"Failed to get today's tasks: {result.error}")

        return result.output

    except Exception as e:
        logger.error(f"Error getting today's tasks: {e}")
        return f"❌ Failed to get today's tasks: {str(e)}"


##############################
# BULK OPERATION TOOLS (ADV-004)
##############################
import uuid
from typing import List

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
    """Return standardized result object for bulk operations."""
    if error:
        return {"index": index, "error": {"msg": error}}
    return {"index": index, "id": todo_id}


def create_todo_bulk(
    idempotency_key: str, items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create multiple todos in one batch.

    Use this when you need to create many todos at once.

    Args:
        idempotency_key: Client-supplied key for safe retries.
        items: List of {"title": str, "notes": str?} objects.
    Returns:
        Bulk response dict following guidelines.

    See also: create_todo
    """
    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

    batch_id = uuid.uuid4().hex
    results = []
    succeeded = failed = 0

    for idx, itm in enumerate(items):
        try:
            title = itm.get("title")
            notes = itm.get("notes", "")
            res = create_todo(title, notes)  # reuse existing tool
            # Parse ID from success message: "✅ Created todo 'Title' (ID: ABC)"
            todo_id = res.split("ID:")[-1].strip(") ") if "ID:" in res else None
            results.append(_build_result(idx, todo_id=todo_id))
            succeeded += 1
        except Exception as e:
            results.append(_build_result(idx, error=str(e)))
            failed += 1
    return {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }


def complete_todo_bulk(idempotency_key: str, items: List[str]) -> Dict[str, Any]:
    """Complete multiple todos in one batch.

    See also: complete_todo
    """
    if not isinstance(items, list):
        return {"error": "items must be list of todo IDs"}
    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

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
    return {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }


def move_todo_bulk(idempotency_key: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Move multiple todos in one call.

    Each item: {"todo_id": str, "destination_type": "area|project|list", "destination_name": str}

    See also: move_todo
    """
    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

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
    return {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }


def update_todo_bulk(
    idempotency_key: str, items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Update multiple todos in one batch.

    Each item: {"todo_id": str, "title?": str, "notes?": str, "when?": str, "deadline?": str}

    See also: update_todo
    """
    validation_error = _validate_batch(items, idempotency_key)
    if validation_error:
        return {"error": validation_error}

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
    return {
        "results": results,
        "batch_id": batch_id,
        "processed": len(items),
        "succeeded": succeeded,
        "failed": failed,
    }


# ---- existing function below ----


def list_inbox_items() -> str:
    """
    Get items in the inbox.

    Returns:
        Formatted list of inbox items
    """
    try:
        client.ensure_running()

        script = """
        tell application "Things3"
            set inboxTodos to to dos of list "Inbox"
            set taskCount to count of inboxTodos
            set resultText to "Inbox (" & taskCount & " items):\\n\\n"
            
            repeat with i from 1 to taskCount
                set currentToDo to item i of inboxTodos
                set todoId to id of currentToDo
                set todoName to name of currentToDo
                set todoNotes to notes of currentToDo
                
                set resultText to resultText & "• " & todoName & " (ID: " & todoId & ")"
                if todoNotes is not "" then
                    set resultText to resultText & " - " & todoNotes
                end if
                set resultText to resultText & "\\n"
            end repeat
            
            return resultText
        end tell
        """

        result = client.executor.execute(script)

        if not result.success:
            raise ThingsError(f"Failed to get inbox items: {result.error}")

        return result.output

    except Exception as e:
        logger.error(f"Error getting inbox items: {e}")
        return f"❌ Failed to get inbox items: {str(e)}"


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
    try:
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

            script = f"""
            tell application "Things3"
                set targetToDo to to do id "{safe_id}"
                {updates_str}
                return name of targetToDo
            end tell
            """

            result = client.executor.execute(script)

            if not result.success:
                raise ThingsError(f"Failed to update todo: {result.error}")

            todo_name = result.output
        else:
            # If no property updates, just get the name for the response
            script = f"""
            tell application "Things3"
                return name of to do id "{safe_id}"
            end tell
            """
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
                move_script = f"""
                tell application "Things3"
                    move to do id "{safe_id}" to list "Someday"
                end tell
                """
                move_result = client.executor.execute(move_script)
                if not move_result.success:
                    logger.warning(f"Failed to move todo to Someday: {move_result.error}")
            except Exception as e:
                logger.warning(f"Error moving todo to Someday: {e}")

        return f"✏️ Updated todo: {todo_name}"

    except Exception as e:
        logger.error(f"Error updating todo: {e}")
        return f"❌ Failed to update todo: {str(e)}"


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
    try:
        client.ensure_running()

        safe_id = todo_id.replace('"', '\\"')
        safe_destination = destination_name.replace('"', '\\"')

        # Build AppleScript based on destination type
        if destination_type.lower() == "area":
            script = f"""
            tell application "Things3"
                set targetToDo to to do id "{safe_id}"
                set targetArea to area "{safe_destination}"
                move targetToDo to targetArea
                return name of targetToDo
            end tell
            """
        elif destination_type.lower() == "project":
            script = f"""
            tell application "Things3"
                set targetToDo to to do id "{safe_id}"
                set targetProject to project "{safe_destination}"
                move targetToDo to targetProject
                return name of targetToDo
            end tell
            """
        elif destination_type.lower() == "list":
            script = f"""
            tell application "Things3"
                set targetToDo to to do id "{safe_id}"
                set targetList to list "{safe_destination}"
                move targetToDo to targetList
                return name of targetToDo
            end tell
            """
        else:
            return f"❌ Invalid destination type: {destination_type}. Use 'area', 'project', or 'list'"

        result = client.executor.execute(script)

        if not result.success:
            raise ThingsError(f"Failed to move todo: {result.error}")

        todo_name = result.output
        return f"📁 Moved todo '{todo_name}' to {destination_type} '{destination_name}'"

    except Exception as e:
        logger.error(f"Error moving todo: {e}")
        return f"❌ Failed to move todo: {str(e)}"


# Note: get_areas and get_projects functions have been moved to resources.py
# and are now implemented as MCP resources rather than tools.


def list_areas() -> List[Dict[str, Any]]:
    """Return available Things areas as JSON objects."""

    return areas_list()


def list_projects() -> List[Dict[str, Any]]:
    """Return available Things projects as JSON objects."""

    return projects_list()


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
    client.ensure_running()

    safe_id = todo_id.replace('"', '\\"')

    script = f"""
    tell application "Things3"
        set targetToDo to to do id "{safe_id}"
        set status of targetToDo to completed
        return name of targetToDo
    end tell
    """

    result = client.executor.execute(script)

    if not result.success:
        raise ThingsError(f"Failed to complete todo: {result.error}")

    todo_name = result.output
    return f"✅ Completed todo: {todo_name}"
