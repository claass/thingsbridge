"""Main MCP server for Things 3 integration."""

from fastmcp import FastMCP
from fastmcp.prompts import Prompt

from .resources import areas_list, inbox_items, projects_list, today_tasks
from .tools import (
    complete_todo,
    complete_todo_bulk,
    create_project,
    create_todo,
    create_todo_bulk,
    list_areas,
    list_inbox_items,
    list_projects,
    list_today_tasks,
    move_todo,
    move_todo_bulk,
    search_due_this_week,
    search_overdue,
    search_scheduled_this_week,
    search_todo,
    update_todo,
    update_todo_bulk,
)

# Initialize the MCP server
mcp = FastMCP("Things Bridge 🚀")


def _hello_things() -> str:
    """Test function to verify server is working."""
    return "Hello from Things Bridge! 🎯"


# Register test tool
hello_things = mcp.tool(
    _hello_things,
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    tags={"action"},
)

# Register core MCP tools
create_todo_tool = mcp.tool(
    create_todo,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    },
    tags={"action"},
)
create_project_tool = mcp.tool(
    create_project,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    },
    tags={"action"},
)
update_todo_tool = mcp.tool(
    update_todo,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
    },
    tags={"action", "destructive"},
)
search_todo_tool = mcp.tool(
    search_todo,
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    tags={"search"},
)
list_today_tasks_tool = mcp.tool(
    list_today_tasks,
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    tags={"listing"},
)
list_inbox_items_tool = mcp.tool(
    list_inbox_items,
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    tags={"listing"},
)
# list_* wrappers
list_areas_tool = mcp.tool(
    list_areas,
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    tags={"listing"},
)
list_projects_tool = mcp.tool(
    list_projects,
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    tags={"listing"},
)
complete_todo_tool = mcp.tool(
    complete_todo,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
    },
    tags={"action", "destructive"},
)
move_todo_tool = mcp.tool(
    move_todo,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
    },
    tags={"action", "destructive"},
)
# Register bulk operation tools
create_bulk_tool = mcp.tool(
    create_todo_bulk,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    tags={"batch", "action"},
)
update_bulk_tool = mcp.tool(
    update_todo_bulk,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
    },
    tags={"batch", "action", "destructive"},
)
move_bulk_tool = mcp.tool(
    move_todo_bulk,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
    },
    tags={"batch", "action", "destructive"},
)
complete_bulk_tool = mcp.tool(
    complete_todo_bulk,
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
    },
    tags={"batch", "action", "destructive"},
)

# Register date-based search tools
search_due_this_week_tool = mcp.tool(
    search_due_this_week,
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    tags={"search", "date-range"},
)
search_scheduled_this_week_tool = mcp.tool(
    search_scheduled_this_week,
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    tags={"search", "date-range"},
)
search_overdue_tool = mcp.tool(
    search_overdue,
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    tags={"search", "date-range"},
)


# Register MCP resources using correct FastMCP syntax
@mcp.resource(
    uri="things://areas",
    name="Things Areas",
    description="List of available areas in Things 3",
    mime_type="application/json",
)
def get_areas():
    return areas_list()


@mcp.resource(
    uri="things://projects",
    name="Things Projects",
    description="List of available projects in Things 3",
    mime_type="application/json",
)
def get_projects():
    return projects_list()


@mcp.resource(
    uri="things://today",
    name="Today's Tasks",
    description="Today's scheduled tasks in Things 3",
    mime_type="application/json",
)
def get_today():
    return today_tasks()


@mcp.resource(
    uri="things://inbox",
    name="Inbox Items",
    description="Items in Things 3 inbox",
    mime_type="application/json",
)
def get_inbox():
    return inbox_items()


# Register prompt resources for better tool usage guidance
@mcp.prompt(
    name="update_todo_help",
    description="Get guidance on using the update_todo tool with examples"
)
def update_todo_guidance(field_to_update: str = "all") -> str:
    """
    Provide detailed guidance on using the update_todo tool.
    
    Args:
        field_to_update: Which field you want to update (title, notes, when, deadline, all)
    """
    base_guidance = """
# How to Use update_todo Tool

The update_todo tool modifies existing todos in Things 3. You only need to specify the fields you want to change.

## Required Parameter:
- **todo_id**: Get this from search_todo, list_today_tasks, or list_inbox_items

## Optional Parameters (only specify what you want to change):
"""
    
    if field_to_update in ["title", "all"]:
        base_guidance += """
### title: Change the todo name
- Example: `update_todo("ABC123", title="Updated task name")`
"""
    
    if field_to_update in ["notes", "all"]:
        base_guidance += """
### notes: Update todo description
- Add notes: `update_todo("ABC123", notes="Additional details")`
- Clear notes: `update_todo("ABC123", notes="")`
- Keep current notes: Don't specify notes parameter
"""
    
    if field_to_update in ["when", "all"]:
        base_guidance += """
### when: Set start date (when item becomes available to work on)
- Available today: `update_todo("ABC123", when="today")`
- Available tomorrow: `update_todo("ABC123", when="tomorrow")`
- No specific start date: `update_todo("ABC123", when="someday")`
- Available from specific date: `update_todo("ABC123", when="2024-07-01")`
- Keep current start date: Don't specify when parameter
"""
    
    if field_to_update in ["deadline", "all"]:
        base_guidance += """
### deadline: Set due date (when task must be completed)
- Set due date: `update_todo("ABC123", deadline="2024-07-10")`
- Keep current due date: Don't specify deadline parameter
"""
    
    base_guidance += """
## Common Workflows:

1. **Find a todo first:**
   ```
   search_todo("meeting")  # Find todos with "meeting" in title
   ```

2. **Application example (available July 1st, due July 10th):**
   ```
   update_todo("ABC123", title="Submit application", when="2024-07-01", deadline="2024-07-10")
   ```

3. **Make available today with deadline:**
   ```
   update_todo("ABC123", when="today", deadline="2024-12-31")
   ```

4. **Update just start date:**
   ```
   update_todo("ABC123", when="tomorrow")  # Available tomorrow
   ```

Remember: Only specify parameters for fields you want to change!
"""
    
    return base_guidance


@mcp.prompt(
    name="things_workflow_help", 
    description="Get guidance on common Things 3 workflows using the MCP tools"
)
def things_workflow_guidance(workflow: str = "overview") -> str:
    """
    Provide guidance on common Things 3 workflows.
    
    Args:
        workflow: Type of workflow (overview, inbox_processing, project_management, daily_planning)
    """
    
    if workflow == "inbox_processing":
        return """
# Inbox Processing Workflow

1. **View inbox items:**
   ```
   list_inbox_items()
   ```

2. **For each item, decide:**
   - **Quick task (< 2 min):** Complete immediately with `complete_todo("ID")`
   - **Schedule:** Use `update_todo("ID", when="today")` or specific date
   - **Add to project:** Use `move_todo("ID", "project", "Project Name")`
   - **Add context:** Use `update_todo("ID", notes="Additional context")`

3. **Clear the inbox:** Process until `list_inbox_items()` shows 0 items
"""
    
    elif workflow == "project_management":
        return """
# Project Management Workflow

1. **Create a project:**
   ```
   create_project("Project Name", area="Work", notes="Project description")
   ```

2. **Add tasks to project:**
   ```
   create_todo("Task 1", list_name="Project Name")
   create_todo("Task 2", list_name="Project Name")
   ```

3. **View all projects:**
   ```
   list_projects()  # See all available projects
   ```

4. **Move existing todos to project:**
   ```
   move_todo("TODO_ID", "project", "Project Name")
   ```
"""
    
    elif workflow == "daily_planning":
        return """
# Daily Planning Workflow

1. **Review today's tasks:**
   ```
   list_today_tasks()
   ```

2. **Make important items available today:**
   ```
   search_todo("urgent")  # Find urgent items
   update_todo("ID", when="today")  # Make available to work on today
   ```

3. **Set deadlines:**
   ```
   update_todo("ID", deadline="2024-12-31")
   ```

4. **Process inbox:**
   ```
   list_inbox_items()  # See what needs processing
   ```
"""
    
    else:  # overview
        return """
# Things 3 MCP Workflows Overview

## Available Workflows:
- **inbox_processing**: Clear and organize your inbox
- **project_management**: Create and manage projects
- **daily_planning**: Plan your day effectively

## Quick Reference:
- `list_today_tasks()` - See today's schedule
- `list_inbox_items()` - Process inbox
- `search_todo("keyword")` - Find specific todos
- `search_due_this_week()` - Find tasks due this week
- `search_overdue()` - Find overdue tasks
- `create_todo("title", when="today")` - Add new task
- `update_todo("ID", when="tomorrow")` - Reschedule
- `complete_todo("ID")` - Mark done

Use specific workflow prompts for detailed guidance!
"""


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
