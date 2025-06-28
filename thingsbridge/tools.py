"""Main tools module - imports from all specialized modules."""

# Import all tools from specialized modules
from .core_tools import (
    complete_todo,
    create_project,
    create_todo,
    move_todo,
    update_todo,
)
from .search_tools import (
    list_areas,
    list_inbox_items,
    list_projects,
    list_today_tasks,
    search_due_this_week,
    search_overdue,
    search_scheduled_this_week,
    search_todo,
)
from .bulk_tools import (
    complete_todo_bulk,
    create_todo_bulk,
    move_todo_bulk,
    update_todo_bulk,
)

# Re-export all functions for backward compatibility
__all__ = [
    # Core CRUD operations
    "create_todo",
    "create_project", 
    "update_todo",
    "complete_todo",
    "move_todo",
    # Search and listing
    "search_todo",
    "search_due_this_week",
    "search_scheduled_this_week",
    "search_overdue",
    "list_today_tasks",
    "list_inbox_items",
    "list_areas",
    "list_projects",
    # Bulk operations
    "create_todo_bulk",
    "update_todo_bulk",
    "complete_todo_bulk",
    "move_todo_bulk",
]