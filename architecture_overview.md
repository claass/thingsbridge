# ThingsBridge Architecture Overview

## Module Relationship Diagram

```
                                  📡 MCP PROTOCOL
                                        │
┌─────────────────────────────────────────────────────────────────────────┐
│                           🚀 ENTRY POINT LAYER                         │
├─────────────────────────────────────────────────────────────────────────┤
│                              server.py                                 │
│                      (FastMCP Server - 594 lines)                      │
│                   • MCP tool registration & routing                    │
│                   • Resource definitions (things://)                   │
│                   • Prompt resources for guidance                      │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────────┐
│                           🎭 FACADE LAYER                              │
├─────────────────────────────────────────────────────────────────────────┤
│                              tools.py                                  │
│                        (Import Facade - 84 lines)                     │
│                   • Re-exports all tool functions                      │
│                   • Backward compatibility interface                   │
│                   • Optional import handling                           │
└─────────────────────────┬───┬───────────┬───────────────────────────────┘
                          │   │           │
        ┌─────────────────┘   │           └─────────────────┐
        │                     │                             │
        ▼                     ▼                             ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  🔧 CRUD     │    │  🔍 SEARCH   │    │  ⚡ BULK     │    │  📋 RESOURCES│
│              │    │              │    │              │    │              │
│core_tools.py │    │search_tools  │    │bulk_tools.py │    │resources.py  │
│  540 lines   │    │   .py        │    │  750 lines   │    │  230 lines   │
│              │    │  335 lines   │    │              │    │              │
│• create_*    │    │• search_*    │    │• *_bulk      │    │• areas_list  │
│• update_*    │    │• list_*      │    │• idempotency │    │• today_tasks │
│• complete_*  │    │• date ranges │    │• 5-10x speed │    │• inbox_items │
│• cancel_*    │    │• filtering   │    │• batch ops   │    │• projects    │
│• delete_*    │    │• caching     │    │• fallbacks   │    │• caching     │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       └───────────────────┼───────────────────┼───────────────────┘
                           │                   │
                           ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      🛠️ APPLESCRIPT LAYER                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐    │
│  │    applescript_builder.py   │    │         things3.py          │    │
│  │        (716 lines)          │    │        (108 lines)         │    │
│  │                             │    │                             │    │
│  │  • Modular script building  │    │  • Things3Client wrapper    │    │
│  │  • Template generation      │    │  • Connection management    │    │
│  │  • String sanitization      │    │  • Process checking         │    │
│  │  • Batch script assembly    │    │  • Global client instance   │    │
│  │  • Property handling        │    │  • Version info             │    │
│  └─────────────┬───────────────┘    └─────────────┬───────────────┘    │
│                │                                  │                    │
└────────────────┼──────────────────────────────────┼────────────────────┘
                 │                                  │
                 └──────────────┬───────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        ⚙️ CORE SYSTEMS LAYER                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│ │applescript.py│  │   cache.py   │  │   utils.py   │  │   tests/     │ │
│ │  (93 lines)  │  │ (236 lines)  │  │ (186 lines)  │  │ (11 files)   │ │
│ │              │  │              │  │              │  │              │ │
│ │• Executor    │  │• TTLCache    │  │• Error       │  │• Cleanup     │ │
│ │• Results     │  │• ShelveCache │  │  handling    │  │  system      │ │
│ │• Timeouts    │  │• Decorators  │  │• Date utils  │  │• Coverage    │ │
│ │• Error       │  │• 37,000x     │  │• Validation  │  │• Integration │ │
│ │  handling    │  │  speedup     │  │• Formatting  │  │• Edge cases  │ │
│ │• Logging     │  │• Threading   │  │• Scheduling  │  │• Mocking     │ │
│ └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                           🍎 THINGS 3 APP
```

## Key Architectural Patterns

### 1. **Layered Architecture**
- **Entry**: MCP protocol handling
- **Facade**: Unified tool interface  
- **Tools**: Business logic modules
- **AppleScript**: Script generation & execution
- **Core**: Shared utilities & caching

### 2. **Module Relationships**

```
Import Dependencies:
server.py → tools.py → {core_tools, search_tools, bulk_tools, resources}
                    ↓
All tools → applescript_builder.py → applescript.py → things3.py
         ↓
All tools → {cache.py, utils.py}
```

### 3. **Data Flow**

```
MCP Request → server.py → tools.py → specific_tool.py
                                          ↓
AppleScript Generation ← applescript_builder.py
                                          ↓
Cache Check ← cache.py               Execution → things3.py
     ↓                                    ↓
Cache Hit → Return                   AppleScript → Things 3
     ↓                                    ↓
Response ← Format ← Parse ← AppleScript Result
```

## Performance Optimizations

### 🚀 **Speed Improvements**
- **Bulk Operations**: 5-10x faster than individual calls
- **Resource Caching**: 37,000x - 54,000x speed improvement  
- **Batch AppleScript**: ~40ms for 500 items
- **TTL Caching**: 5-minute resource cache

### 💾 **Caching Strategy**
```
┌─────────────────┐    ┌─────────────────┐
│   TTLCache      │    │   ShelveCache   │
│ (In-Memory)     │    │  (Persistent)   │
│                 │    │                 │
│ • 5min TTL      │    │ • create_todo   │
│ • areas/        │    │   idempotency   │
│   projects/     │    │ • bulk ops      │
│   tags          │    │ • cross-session │
│ • Thread-safe   │    │ • disk-based    │
└─────────────────┘    └─────────────────┘
```

## Module Purposes

| Module | Purpose | Lines | Key Features |
|--------|---------|-------|--------------|
| `server.py` | MCP entry point | 594 | FastMCP server, tool registration |
| `tools.py` | Import facade | 84 | Re-exports, compatibility |
| `core_tools.py` | CRUD operations | 540 | create, update, complete, delete |
| `search_tools.py` | Search & lists | 335 | Advanced filtering, date ranges |
| `bulk_tools.py` | Batch operations | 750 | High-performance bulk ops |
| `resources.py` | MCP resources | 230 | Cached data providers |
| `applescript_builder.py` | Script generation | 716 | Modular AppleScript building |
| `things3.py` | Things 3 client | 108 | Connection, process management |
| `applescript.py` | Script executor | 93 | Low-level AppleScript execution |
| `cache.py` | Caching system | 236 | TTL + persistent caching |
| `utils.py` | Shared utilities | 186 | Error handling, validation |

## Testing Infrastructure

```
tests/
├── conftest.py              # pytest config + cleanup
├── test_cleanup.py          # Cleanup tracker system  
├── test_helpers.py          # Tracked creation functions
├── test_*.py (8 files)      # Comprehensive coverage
└── Cleanup System:
    ├── Auto-tracking test artifacts
    ├── Session-level cleanup  
    ├── Persistent cleanup logs
    └── Thread-safe operations
```

The architecture is designed for **maintainability**, **performance**, and **extensibility** with clear separation of concerns and robust error handling throughout.