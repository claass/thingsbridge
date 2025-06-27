"""Basic tests for the MCP server."""

import pytest
from thingsbridge.server import mcp

def test_server_creation():
    """Test that the server can be created."""
    assert mcp.name == "Things Bridge 🚀"

def test_hello_things():
    """Test the hello_things tool."""
    # Test that the raw function works
    from thingsbridge.server import _hello_things
    result = _hello_things()
    assert isinstance(result, str)
    assert "Hello from Things Bridge!" in result