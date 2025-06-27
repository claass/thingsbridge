#!/usr/bin/env python3
"""
Test MCP resources using FastMCP's built-in Inspector capabilities.

This script demonstrates how to use FastMCP's dev mode and Inspector
to debug resource registration and test resource functionality.
"""

import sys
import json
import asyncio
import subprocess
import time
import webbrowser
from pathlib import Path

def start_mcp_inspector():
    """
    Start the MCP Inspector for debugging resources.
    
    Uses the FastMCP CLI dev command to start the server with Inspector.
    """
    print("🚀 Starting MCP Inspector...")
    print("=" * 50)
    
    # Get the current directory
    current_dir = Path(__file__).parent
    server_file = current_dir / "thingsbridge" / "server.py"
    
    if not server_file.exists():
        print(f"❌ Server file not found: {server_file}")
        return None
    
    print(f"📂 Server file: {server_file}")
    print("🔧 Starting FastMCP dev server with Inspector...")
    
    try:
        # Start the MCP Inspector
        # The format is: fastmcp dev path/to/file.py:server_variable
        cmd = [
            sys.executable, "-m", "fastmcp", "dev", 
            f"{server_file}:mcp"
        ]
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        print("\n" + "=" * 50)
        print("🌐 MCP Inspector should open in your browser")
        print("📍 URL: http://127.0.0.1:6274")
        print("=" * 50)
        print("\n📋 In the Inspector, you can:")
        print("• Click the 'Resources' tab to see registered resources")
        print("• Test each resource by clicking on it")
        print("• View the JSON response from each resource")
        print("• Compare with Tools tab to see the difference")
        print("\n🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Run the command
        process = subprocess.run(cmd, cwd=current_dir)
        return process.returncode == 0
        
    except KeyboardInterrupt:
        print("\n\n🛑 Inspector stopped by user")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Inspector: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_fastmcp_installation():
    """Check if FastMCP is installed and get version info."""
    print("🔍 Checking FastMCP Installation...")
    print("=" * 50)
    
    try:
        # Check if fastmcp command is available
        result = subprocess.run([sys.executable, "-m", "fastmcp", "--version"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ FastMCP installed: {version}")
            
            # Check if it's a recent enough version for dev command
            if "dev" in subprocess.run([sys.executable, "-m", "fastmcp", "--help"], 
                                     capture_output=True, text=True).stdout:
                print("✅ FastMCP dev command available")
                return True
            else:
                print("❌ FastMCP dev command not available (need newer version)")
                return False
        else:
            print(f"❌ FastMCP not properly installed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ FastMCP command timed out")
        return False
    except FileNotFoundError:
        print("❌ FastMCP not found - is it installed?")
        print("💡 Try: pip install fastmcp")
        return False
    except Exception as e:
        print(f"❌ Error checking FastMCP: {e}")
        return False

def test_server_import():
    """Test that the server can be imported successfully."""
    print("🔍 Testing Server Import...")
    print("=" * 50)
    
    try:
        from thingsbridge.server import mcp
        print(f"✅ Server imported successfully: {mcp.name}")
        
        # Check if resources are registered
        if hasattr(mcp, '_resource_manager'):
            print("✅ Resource manager found")
            return True
        else:
            print("❌ Resource manager not found")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import server: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error importing server: {e}")
        return False

def provide_manual_testing_guide():
    """Provide a guide for manual testing of MCP resources."""
    print("📖 Manual Testing Guide")
    print("=" * 50)
    
    guide = """
🔧 Using MCP Inspector:

1. Start the Inspector:
   python test_mcp_inspector.py

2. In the Inspector UI:
   • Click the 'Resources' tab
   • You should see 4 resources:
     - things://areas (Things Areas)
     - things://projects (Things Projects) 
     - things://today (Today's Tasks)
     - things://inbox (Inbox Items)

3. Test each resource:
   • Click on a resource name
   • View the JSON response
   • Check for errors

4. Compare with Tools:
   • Click the 'Tools' tab
   • Notice how tools are presented differently
   • Tools have parameter forms, resources just return data

🔧 Using Claude Desktop:

1. Ensure your config is correct:
   ~/Library/Application Support/Claude/claude_desktop_config.json

2. Restart Claude Desktop completely

3. Test resource awareness:
   • Ask: "What resources do you have access to?"
   • Ask: "List my Things areas and projects"
   • Try: "Show me today's tasks from Things"

🔧 Command Line Testing:

You can also test MCP protocol directly with JSON-RPC:

echo '{"jsonrpc":"2.0","method":"resources/list","id":1}' | python -c "
import sys, json
from thingsbridge.server import mcp
import asyncio

async def test():
    if hasattr(mcp, '_resource_manager'):
        resources = await mcp._resource_manager.get_resources()
        result = []
        for uri, resource in resources.items():
            result.append({
                'uri': uri,
                'name': getattr(resource, 'name', ''),
                'description': getattr(resource, 'description', ''),
                'mimeType': getattr(resource, 'mime_type', 'text/plain')
            })
        print(json.dumps({'resources': result}, indent=2))

asyncio.run(test())
"
"""
    print(guide)

def main():
    """Main function to run MCP Inspector tests."""
    print("🧪 MCP Inspector Test Suite")
    print("=" * 50)
    
    # Pre-flight checks
    checks = [
        ("FastMCP Installation", check_fastmcp_installation),
        ("Server Import", test_server_import)
    ]
    
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}...")
        if not check_func():
            print(f"\n❌ {check_name} failed. Cannot proceed with Inspector.")
            provide_manual_testing_guide()
            return False
        print()
    
    print("✅ All pre-flight checks passed!")
    print("\n" + "=" * 50)
    
    # Provide options
    print("🎯 Choose testing method:")
    print("1. Start MCP Inspector (recommended)")
    print("2. Show manual testing guide")
    print("3. Exit")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            return start_mcp_inspector()
        elif choice == "2":
            provide_manual_testing_guide()
            return True
        elif choice == "3":
            print("👋 Goodbye!")
            return True
        else:
            print("❌ Invalid choice")
            return False
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)