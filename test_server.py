#!/usr/bin/env python3
"""Test script to verify the MCP server starts correctly."""

import sys
import json
from thingsbridge.server import mcp

async def test_server_startup():
    """Test that the server can be created and has the expected tools."""
    print("🧪 Testing MCP Server Startup...")
    
    # Test server creation
    assert mcp.name == "Things Bridge 🚀"
    print(f"✅ Server name: {mcp.name}")
    
    # Test that tools are registered
    expected_tools = [
        "_hello_things", "create_todo", "create_project", "update_todo",
        "search_things", "get_today_tasks", "get_inbox_items", "complete_todo"
    ]
    
    # Get registered tool names from tool manager
    try:
        tools = await mcp._tool_manager.get_tools()
        # Tools are returned as a dictionary with tool names as keys
        registered_tools = list(tools.keys()) if isinstance(tools, dict) else [str(tool) for tool in tools]
        print(f"📋 Registered tools: {registered_tools}")
        
        for tool in expected_tools:
            if tool in registered_tools:
                print(f"✅ Tool '{tool}' is registered")
            else:
                print(f"❌ Tool '{tool}' is missing")
                return False
        
        print("🎉 All tools are properly registered!")
        return True
    except Exception as e:
        print(f"❌ Error getting tools: {e}")
        return False

def test_things_connection():
    """Test connection to Things 3."""
    print("\n🔗 Testing Things 3 Connection...")
    
    try:
        from thingsbridge.things3 import client
        connection_info = client.test_connection()
        
        if connection_info["connected"]:
            print(f"✅ Connected to {connection_info['app_name']}")
            
            # Test version info
            version_info = client.get_version_info()
            print(f"📱 Things 3 version: {version_info['version']}")
            
            return True
        else:
            print(f"❌ Failed to connect: {connection_info.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Things Bridge MCP Server Test Suite")
    print("=" * 50)
    
    # Test server startup
    server_ok = await test_server_startup()
    
    # Test Things 3 connection
    things_ok = test_things_connection()
    
    print("\n" + "=" * 50)
    if server_ok and things_ok:
        print("🎉 All tests passed! Server is ready for Claude Desktop.")
        print("\nNext steps:")
        print("1. Restart Claude Desktop to load the new MCP server")
        print("2. Look for 'Things Bridge 🚀' in the MCP servers list")
        print("3. Try using commands like 'create a todo' or 'show my inbox'")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))