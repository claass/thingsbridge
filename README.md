# Things Bridge

⚠️ This project is under active development and may be unstable. Errors are expected.

Things Bridge is an [MCP](https://github.com/hearthware/fastmcp) server that lets LLMs automate the Things 3 task manager through AppleScript. It exposes the most common actions as callable tools and also publishes a few read-only resources. Because it is built on **FastMCP**, the server automatically exposes a machine‑readable schema at `/schema` for easy integration with MCP clients and ChatGPT-style tooling.

## Features

- Create, update and complete todos
- Manage projects and areas
- Query inbox and today tasks
- High performance AppleScript bridge using native batch execution (~40ms for a 500 item batch)
- Batch operations for creating, updating, moving and completing items with idempotency keys
- Integrated FastMCP schema and read-only resources for easy tool discovery

## Requirements

- macOS with Things 3 installed
- Python 3.10+

## Installation

Install from source:

```bash
git clone https://github.com/hearthware/thingsbridge.git
cd thingsbridge
pip install -e .
```

## Getting Started

Create a virtual environment and install the development dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

Run the test suite and start the server:

```bash
python -m pytest -v
python -m thingsbridge.server
```

Once running, visit `http://localhost:8000/schema` to view the available tools
and resources.

## Running

After installation the server can be started with the provided console script:

```bash
thingsbridge
```

By default it listens on `localhost:8000`. Use an MCP client such as FastMCP's HTTP interface to call tools. You can inspect all available tools and resources by requesting `http://localhost:8000/schema`.

### Example: bulk create

```bash
curl -X POST http://localhost:8000/tools/create_todo_bulk \
  -H 'Content-Type: application/json' \
  -d '{
        "idempotency_key": "123e4567",
        "items": [
          {"title": "Buy milk", "client_id": "a1"},
          {"title": "Send report", "notes": "due tomorrow", "client_id": "a2"}
        ]
      }' | jq
```


The response schema follows `docs/batch-tools-guidelines.txt` and includes per-item status information.

### Example: list all areas

```bash
curl -X POST http://localhost:8000/tools/list_areas \
  -H 'Content-Type: application/json' \
  -d '{}' | jq
```

This returns JSON data like:

```json
[
  {"name": "Work", "id": "THMArea:XXXXXXXX", "type": "area"},
  {"name": "Personal", "id": "THMArea:YYYYYYYY", "type": "area"}
]
```

Bulk operations always return HTTP 200 with per-item results so you can retry safely. A typical partial success response looks like:

```json
{
  "results": [
    {"index": 0, "todo_id": "THMToDo:123"},
    {"index": 1, "error": "Unknown tag"}
  ],
  "batch_id": "b9f7a…",
  "processed": 2,
  "succeeded": 1,
  "failed": 1
}
```
If the native batch fails entirely, Things Bridge automatically falls back to processing items one by one to ensure completion.

Repeated calls with the same `idempotency_key` return the original
batch result without executing AppleScript again. Provide a unique
`client_id` per item when creating todos to deduplicate partial retries.

Available tools:
* `create_todo`
* `create_project`
* `update_todo`
* `search_todo`
* `search_due_this_week`
* `search_scheduled_this_week`
* `search_overdue`
* `list_today_tasks`
* `list_inbox_items`
* `list_areas`
* `list_projects`
* `complete_todo`
* `move_todo`

Available batch tools:
* `create_todo_bulk`
* `update_todo_bulk`
* `move_todo_bulk`
* `complete_todo_bulk`
* `cancel_todo_bulk`
* `delete_todo_bulk`

### Naming conventions

Tool names follow a simple pattern:
* `list_...` for read-only operations that return collections
* singular verbs (`create_`, `update_`, etc.) for single-item actions
* `*_bulk` suffix for batch versions of those actions

### Extended task and project fields

`create_todo` and `create_project` now accept optional `when`, `deadline`, `tags`, and target lists (`list_name` or `area`). `update_todo` supports the same date fields and lets you clear notes by sending `"notes": ""`.
When a `when` value other than `someday` is provided, the item is automatically scheduled after creation, and any tags are applied for you.

### Available resources

The server also publishes read-only MCP resources:
* `things://areas` – list of all areas
* `things://projects` – list of all projects
* `things://today` – today's scheduled tasks
* `things://inbox` – inbox items

## Development

See `docs/PROJECT_PLAN.md` for the project roadmap.
