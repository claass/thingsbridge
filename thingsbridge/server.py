"""Main MCP server for Things 3 integration."""

from fastmcp import FastMCP
from typing import Optional, List
from .tools import (
    todo_create, project_create, todo_update, todo_search, 
    todo_list_today, todo_list_inbox, todo_complete,
    todo_move,
    todo_create_bulk, todo_update_bulk, todo_move_bulk, todo_complete_bulk
)
from .resources import areas_list, projects_list, today_tasks, inbox_items

# Initialize the MCP server
mcp = FastMCP("Things Bridge 🚀")

def _hello_things() -> str:
    """Test function to verify server is working."""
    return "Hello from Things Bridge! 🎯"

# Register test tool
hello_things = mcp.tool(_hello_things)

# Register core MCP tools
todo_create_tool = mcp.tool(todo_create)
project_create_tool = mcp.tool(project_create)
todo_update_tool = mcp.tool(todo_update)
todo_search_tool = mcp.tool(todo_search)
todo_list_today_tool = mcp.tool(todo_list_today)
todo_list_inbox_tool = mcp.tool(todo_list_inbox)
todo_complete_tool = mcp.tool(todo_complete)
todo_move_tool = mcp.tool(todo_move)
# Register bulk operation tools
create_bulk_tool = mcp.tool(todo_create_bulk)
update_bulk_tool = mcp.tool(todo_update_bulk)
move_bulk_tool = mcp.tool(todo_move_bulk)
complete_bulk_tool = mcp.tool(todo_complete_bulk)
# Register MCP resources using correct FastMCP syntax
@mcp.resource(
    uri="things://areas",
    name="Things Areas",
    description="List of available areas in Things 3",
    mime_type="application/json"
)
def get_areas():
    return areas_list()

@mcp.resource(
    uri="things://projects",
    name="Things Projects", 
    description="List of available projects in Things 3",
    mime_type="application/json"
)
def get_projects():
    return projects_list()

@mcp.resource(
    uri="things://today",
    name="Today's Tasks",
    description="Today's scheduled tasks in Things 3",
    mime_type="application/json"
)
def get_today():
    return today_tasks()

@mcp.resource(
    uri="things://inbox",
    name="Inbox Items", 
    description="Items in Things 3 inbox",
    mime_type="application/json"
)
def get_inbox():
    return inbox_items()

def main():
    """Run the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()