# Things Bridge

⚠️ This project is under active development and may be unstable. Errors are expected.

Things Bridge is an [MCP](https://github.com/hearthware/fastmcp) server that lets LLMs automate the Things 3 task manager through AppleScript. It exposes the most common actions as callable tools and also publishes a few read-only resources.

## Features

- Create, update and complete todos
- Manage projects and areas
- Query inbox and today tasks
- High performance AppleScript bridge
- Batch operations for creating, updating, moving and completing items

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

## Running

After installation the server can be started with the provided console script:

```bash
thingsbridge
```

By default it listens on `localhost:8000`. Use an MCP client such as FastMCP's HTTP interface to call tools.

### Example: bulk create

```bash
curl -X POST http://localhost:8000/tools/create_todo_bulk \
  -H 'Content-Type: application/json' \
  -d '{
        "idempotency_key": "123e4567",
        "items": [
          {"title": "Buy milk"},
          {"title": "Send report", "notes": "due tomorrow"}
        ]
      }' | jq
```


The response schema follows `docs/batch-tools-guidelines.txt` and includes per-item status information.

Available tools:
* `create_todo`
* `create_project`
* `update_todo`
* `search_todo`
* `list_today_tasks`
* `list_inbox_items`
* `complete_todo`
* `move_todo`

Available batch tools:
* `create_todo_bulk`
* `update_todo_bulk`
* `move_todo_bulk`
* `complete_todo_bulk`

## Development

See `docs/PROJECT_PLAN.md` for the project roadmap.
