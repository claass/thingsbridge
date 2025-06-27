"""Tests for Things 3 integration."""

import pytest
from thingsbridge.things3 import Things3Client, ThingsError

# Check if Things 3 is available for testing
def things3_available():
    """Check if Things 3 is available for testing."""
    try:
        client = Things3Client()
        return client.executor.check_things_running() or client.executor.ensure_things_running().success
    except:
        return False

@pytest.fixture
def client():
    """Create a Things 3 client."""
    return Things3Client()

def test_client_creation(client):
    """Test that Things3Client can be created."""
    assert client is not None
    assert client.executor is not None

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_connection(client):
    """Test connection to Things 3."""
    connection_info = client.test_connection()
    
    assert isinstance(connection_info, dict)
    assert "connected" in connection_info
    
    if connection_info["connected"]:
        assert "app_name" in connection_info
        assert connection_info["app_name"] == "Things3"

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_version_info(client):
    """Test getting version information."""
    try:
        version_info = client.get_version_info()
        assert isinstance(version_info, dict)
        assert "version" in version_info
        assert "app_name" in version_info
        assert version_info["app_name"] == "Things 3"
    except ThingsError:
        # If Things 3 is not running, this is expected
        pytest.skip("Things 3 not accessible")

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_inbox_count(client):
    """Test getting inbox count."""
    try:
        count = client.get_inbox_count()
        assert isinstance(count, int)
        assert count >= 0
    except ThingsError:
        # If Things 3 is not running, this is expected
        pytest.skip("Things 3 not accessible")

def test_error_handling(client):
    """Test error handling with invalid operations."""
    # This should fail gracefully
    connection_info = client.test_connection()
    
    if not connection_info["connected"]:
        # Expected when Things 3 is not running
        assert "error" in connection_info
        assert connection_info["app_running"] in [True, False]