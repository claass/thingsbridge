# Things Bridge - MCP Server for Things 3

A Model Context Protocol (MCP) server that enables LLMs to interact with Things 3 task manager via AppleScript.

## Features

- Create and manage todos, projects, and areas
- Search and retrieve tasks
- High-performance AppleScript integration
- Comprehensive error handling
- Easy MCP client integration

## Installation

```bash
pip install thingsbridge
```

## Usage

### Bulk Operations (ADV-004)

The server now exposes high-performance batch endpoints. Example with FastMCP HTTP client:

```bash
curl -X POST http://localhost:8000/tools/todo_create_bulk \
  -H 'Content-Type: application/json' \
  -d '{
        "idempotency_key": "123e4567",
        "items": [
          {"title": "Buy milk"},
          {"title": "Send report", "notes": "due tomorrow"}
        ]
      }' | jq
```

Response shape follows the guidelines in `docs/batch-tools-guidelines.txt`:

```json
{
  "results": [
    {"index": 0, "id": "ABC123"},
    {"index": 1, "id": "DEF456"}
  ],
  "batch_id": "b9f7a…",
  "processed": 2,
  "succeeded": 2,
  "failed": 0
}
```

Available batch tools:
* `todo_create_bulk`
* `todo_update_bulk`
* `todo_move_bulk`
* `todo_complete_bulk`


```bash
thingsbridge
```

## Requirements

- macOS (AppleScript support required)
- Things 3 installed
- Python 3.8+

## Development

See `PROJECT_PLAN.md` for detailed development roadmap.