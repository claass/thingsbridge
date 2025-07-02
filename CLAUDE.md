# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status
**Phase 3 Performance Optimization Complete** (December 28, 2024)

### Recent Session Summary (Latest)
- **Repository Sync**: Successfully merged latest remote changes including new bulk tools (cancel_todo_bulk, delete_todo_bulk)
- **Test Infrastructure**: Implemented comprehensive test cleanup system to prevent Things 3 artifact pollution
- **Cleanup System**: Automatic tracking and removal of test artifacts with session-level pytest fixtures
- **Test Coverage**: Enhanced bulk operations tests with live testing for cancel/delete operations
- **Merge Resolution**: Resolved conflicts from concurrent development, updated emoji consistency

### Previous Session Summary
- **Major Feature Expansion**: Implemented 8 high-value missing tools (cancel, tags, delete, lists)
- **Performance Breakthrough**: Completed Phase 3 resource caching with TTL (37,000x - 54,000x speed improvement)
- **Architecture**: Thread-safe caching system with smart invalidation for areas/projects/tags
- **Testing**: Added 21 comprehensive tests (12 new tools + 9 cache tests)
- **Coverage**: Increased from ~65% to ~85% of Things 3 automation capabilities

### Previous Major Work Completed
- **Phase 2 Complete**: Split monolithic 1003-line tools.py into 5 focused modules
- **Phase 3 Started**: Implemented native batch AppleScript operations for 5-10x performance improvement
- **Architecture**: Created modular AppleScript generation utilities and centralized validation
- **Testing**: Added comprehensive edge case coverage (64 tests passing)
- **Performance**: Bulk operations now use single AppleScript executions instead of N individual calls

### Current Architecture
- `core_tools.py` (427 lines) - CRUD operations (create, update, complete, move)
- `search_tools.py` (303 lines) - Search and listing functions  
- `bulk_tools.py` (173 lines) - High-performance bulk operations
- `utils.py` (137 lines) - Shared helpers, validation, and utilities
- `applescript_builder.py` (528 lines) - Modular AppleScript generation
- `tools.py` (49 lines) - Import facade for backward compatibility

### Remaining Phase 3 Tasks (Lower Priority)
- ✅ **Resource caching with TTL** - COMPLETE! (37,000x-54,000x performance improvement achieved)
- 🚧 **String processing optimizations** (improve AppleScript JSON generation)
- 🚧 **Pre-compiled script templates** (20-30% execution time reduction)

Phase 3 Priority #1 complete! Major performance gains achieved through intelligent caching.

## Development Commands
```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python -m pytest tests/ -v

# Run server
python -m thingsbridge.server
```

## Architecture Overview
- **FastMCP Server**: Main MCP protocol handler using FastMCP 2.9.2
- **AppleScript Bridge**: Executes Things 3 commands via subprocess
- **Python 3.10+**: Required for FastMCP compatibility

The `server.py` module boots the FastMCP server and registers all
available tools and resources. Individual tool implementations live in
`core_tools.py`, `search_tools.py`, and `bulk_tools.py`. These modules
construct AppleScript snippets via helpers in `applescript_builder.py`
and execute them through `applescript.py`. Results are cached using the
utilities in `cache.py` and exposed as MCP resources via functions in
`resources.py`. The lightweight `tools.py` file re-exports all public
tool functions for backward compatibility.

## Project Progress
- Check PROJECT_PLAN.md for detailed progress tracking
- Update checkboxes as tasks are completed

## MCP Server Configuration

The Things Bridge MCP server is configured in Claude Desktop at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

Configuration:
```json
{
  "mcpServers": {
    "thingsbridge": {
      "command": "/Users/ldc/Desktop/hearthware/thingsbridge/venv/bin/thingsbridge",
      "args": [],
      "cwd": "/Users/ldc/Desktop/hearthware/thingsbridge",
      "env": {},
      "allowedFeatures": {
        "resources": true
      }
    }
  }
}
```

**Important:** The `"allowedFeatures": {"resources": true}` setting is required for Claude Desktop to access MCP resources. Restart Claude Desktop after making config changes.

## Available MCP Tools

### Core Tools
- `create_todo` - Create new tasks with scheduling and tags
- `create_project` - Create new projects with areas
- `update_todo` - Modify existing tasks
- `complete_todo` - Mark tasks as completed
- `cancel_todo` - Mark tasks as canceled (distinct from completed)
- `cancel_project` - Mark projects as canceled (distinct from completed)
- `delete_todo` - Delete tasks (move to trash)
- `delete_project` - Delete projects (move to trash)
- `move_todo` - Move tasks between areas, projects, and lists
- `search_todo` - Find tasks and projects with advanced filtering (including date ranges)
- `list_today_tasks` - Retrieve today's scheduled items
- `list_inbox_items` - Access inbox contents
- `list_anytime_tasks` - Get Anytime list items
- `list_someday_tasks` - Get Someday list items
- `list_upcoming_tasks` - Get Upcoming list items
- `list_logbook_items` - Get completed items from Logbook
- `list_areas` - Get available areas (cached for performance)
- `list_projects` - Get available projects (cached for performance)

### Tag Management Tools
- `create_tag` - Create new tags with optional parent relationships
- `list_tags` - Get all available tags with hierarchy info (cached for performance)

### Date-Based Search Tools
- `search_due_this_week` - Find all tasks due in the next 7 days
- `search_scheduled_this_week` - Find all tasks scheduled in the next 7 days
- `search_overdue` - Find all overdue tasks (due before today)

### Bulk Operation Tools
- `create_todo_bulk` - Create multiple tasks in one batch
- `update_todo_bulk` - Update multiple tasks in one batch
- `complete_todo_bulk` - Complete multiple tasks in one batch
- `move_todo_bulk` - Move multiple tasks in one batch

### Test Tool
- `hello_things` - Test server connectivity

## Available MCP Resources

- `things://areas` - List of available areas in Things 3
- `things://projects` - List of available projects in Things 3  
- `things://today` - Today's scheduled tasks in Things 3
- `things://inbox` - Items in Things 3 inbox

## Testing

Run the comprehensive test suite:
```bash
source venv/bin/activate
python -m pytest tests/ -v
```

Test files:
- `test_tools.py` - Core functionality and scheduling tests
- `test_edge_cases.py` - Edge cases and error handling
- `test_bulk_tools.py` - Bulk operation performance tests
- `test_server.py` - Server and integration tests

## Session Handoff Protocol

When ending a session with Claude Code:
1. **Update CLAUDE.md** with session summary and remaining tasks
2. **Commit and push** all changes to preserve work
3. **Note key context** that will be lost between sessions
4. **Prioritize next steps** for seamless continuation

This ensures smooth handoffs between Claude Code sessions since conversation context is not preserved across restarts.