"""Main MCP server for Things 3 integration."""

from fastmcp import FastMCP

from .resources import areas_list, inbox_items, projects_list, today_tasks
from .tools import (
    complete_todo,
    complete_todo_bulk_auto,
    create_project,
    create_todo,
    create_todo_bulk_auto,
    list_areas,
    list_inbox_items,
    list_projects,
    list_today_tasks,
    move_todo,
    move_todo_bulk_auto,
    search_todo,
    update_todo,
    update_todo_bulk_auto,
)

# Initialize the MCP server
mcp = FastMCP("Things Bridge 🚀")


def _hello_things() -> str:
    """Test function to verify server is working."""
    return "Hello from Things Bridge! 🎯"


# Register test tool
hello_things = mcp.tool(_hello_things)

# Register core MCP tools
create_todo_tool = mcp.tool(create_todo)
create_project_tool = mcp.tool(create_project)
update_todo_tool = mcp.tool(update_todo)
search_todo_tool = mcp.tool(search_todo)
list_today_tasks_tool = mcp.tool(list_today_tasks)
list_inbox_items_tool = mcp.tool(list_inbox_items)
# list_* wrappers
list_areas_tool = mcp.tool(
    list_areas,
    annotations={"readOnlyHint": True},
    tags={"listing"},
)
list_projects_tool = mcp.tool(
    list_projects,
    annotations={"readOnlyHint": True},
    tags={"listing"},
)
complete_todo_tool = mcp.tool(complete_todo)
move_todo_tool = mcp.tool(move_todo)
# Register bulk operation tools with auto-generated keys
create_bulk_tool = mcp.tool(
    create_todo_bulk_auto, exclude_args=["idempotency_key"]
)
update_bulk_tool = mcp.tool(
    update_todo_bulk_auto, exclude_args=["idempotency_key"]
)
move_bulk_tool = mcp.tool(
    move_todo_bulk_auto, exclude_args=["idempotency_key"]
)
complete_bulk_tool = mcp.tool(
    complete_todo_bulk_auto, exclude_args=["idempotency_key"]
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


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
