"""Tests for AppleScript execution utilities."""

import pytest
from thingsbridge.applescript import AppleScriptExecutor, AppleScriptResult

def test_applescript_executor_creation():
    """Test that AppleScriptExecutor can be created."""
    executor = AppleScriptExecutor()
    assert executor.timeout == 30

def test_simple_applescript_execution():
    """Test basic AppleScript execution."""
    executor = AppleScriptExecutor()
    
    # Test simple math operation
    script = 'return 2 + 2'
    result = executor.execute(script)
    
    assert isinstance(result, AppleScriptResult)
    assert result.success is True
    assert result.output == "4"
    assert result.error is None or result.error == ""
    assert result.exit_code == 0

def test_applescript_error_handling():
    """Test AppleScript error handling."""
    executor = AppleScriptExecutor()
    
    # Test script with syntax error
    script = 'this is not valid applescript'
    result = executor.execute(script)
    
    assert isinstance(result, AppleScriptResult)
    assert result.success is False
    assert result.error is not None
    assert result.exit_code != 0

def test_system_events_access():
    """Test that we can access System Events (basic macOS integration)."""
    executor = AppleScriptExecutor()
    
    # Test getting current date - this should work on any macOS system
    script = 'return (current date) as string'
    result = executor.execute(script)
    
    assert isinstance(result, AppleScriptResult)
    assert result.success is True
    assert len(result.output) > 0
    assert result.exit_code == 0