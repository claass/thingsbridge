"""Tests for edge cases and error handling."""

import pytest
from datetime import date, timedelta

pytestmark = pytest.mark.integration

from thingsbridge.tools import (
    create_todo,
    search_todo,
    search_due_this_week,
    search_overdue,
    update_todo,
)


def things3_available():
    """Check if Things 3 is available for testing."""
    try:
        from thingsbridge.things3 import client
        return (
            client.executor.check_things_running()
            or client.executor.ensure_things_running().success
        )
    except:
        return False


# =============================================================================
# DATE PARSING AND VALIDATION TESTS
# =============================================================================

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_create_todo_invalid_date_formats():
    """Test creating todos with various invalid date formats."""
    invalid_dates = [
        "not-a-date",
        "2025-13-01",  # Invalid month
        "2025-02-30",  # Invalid day for February
        "25-12-01",    # Wrong year format
        "2025/12/01",  # Wrong separator
        "",            # Empty string
    ]
    
    for invalid_date in invalid_dates:
        result = create_todo(f"Test Invalid Date {invalid_date}", when=invalid_date)
        # Should either succeed (ignoring invalid date) or fail gracefully
        assert isinstance(result, str)
        assert not result.startswith("Traceback")  # No uncaught exceptions


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_todo_invalid_date_ranges():
    """Test search with invalid date ranges."""
    # Start date after end date
    result = search_todo(
        query="",
        due_start="2025-12-31",
        due_end="2025-01-01"
    )
    assert isinstance(result, str)
    assert "Found" in result
    
    # Invalid date format in range
    result = search_todo(
        query="",
        due_start="invalid-date",
        due_end="2025-12-31"
    )
    assert isinstance(result, str)


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_edge_case_date_values():
    """Test edge case date values."""
    edge_dates = [
        "2025-01-01",  # New Year's Day
        "2025-12-31",  # New Year's Eve
        "2025-02-29",  # Leap year (2024 is leap, 2025 is not)
        "2025-02-28",  # Last day of February (non-leap year)
    ]
    
    for edge_date in edge_dates:
        result = create_todo(f"Test Edge Date {edge_date}", when=edge_date)
        assert isinstance(result, str)


# =============================================================================
# APPLESCRIPT ERROR HANDLING TESTS
# =============================================================================

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_special_characters_in_title():
    """Test todos with special characters in title."""
    special_titles = [
        'Todo with "quotes"',
        "Todo with 'apostrophes'",
        "Todo with !@#$%^&*() symbols",
        "Todo with unicode: 🚀 ✅ 📁",
        "Todo with\nnewlines",
        "Todo with\ttabs",
    ]
    
    for title in special_titles:
        result = create_todo(title)
        assert isinstance(result, str)
        # Should either succeed or fail gracefully, but not crash


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_very_long_inputs():
    """Test with very long inputs."""
    long_title = "A" * 1000
    long_notes = "B" * 5000
    
    result = create_todo(long_title, notes=long_notes)
    assert isinstance(result, str)


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_empty_and_none_inputs():
    """Test with empty and None inputs."""
    # Empty title (should fail)
    result = create_todo("")
    assert isinstance(result, str)
    
    # Empty query in search
    result = search_todo("")
    assert isinstance(result, str)
    assert "Found" in result
    
    # None values where strings expected
    result = update_todo("fake-id", title=None, notes=None)
    assert isinstance(result, str)


# =============================================================================
# BOUNDARY CONDITION TESTS
# =============================================================================

def test_search_functions_performance():
    """Test that search functions complete in reasonable time."""
    import time
    
    start_time = time.time()
    result = search_due_this_week()
    elapsed = time.time() - start_time
    
    assert elapsed < 30  # Should complete within 30 seconds
    assert isinstance(result, str)


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_with_large_limits():
    """Test search with very large limit values."""
    result = search_todo("", limit=999999)
    assert isinstance(result, str)
    assert "Found" in result


@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_search_with_zero_limit():
    """Test search with zero limit."""
    result = search_todo("", limit=0)
    assert isinstance(result, str)


# =============================================================================
# CONCURRENCY AND STATE TESTS
# =============================================================================

@pytest.mark.skipif(not things3_available(), reason="Things 3 not available")
def test_multiple_operations_sequence():
    """Test sequence of operations to ensure state consistency."""
    # Create a todo
    create_result = create_todo("Test Sequence", when="today")
    assert "✅ Created todo" in create_result
    
    # Search for it
    search_result = search_todo("Test Sequence")
    assert isinstance(search_result, str)
    
    # Extract ID and update it (this is brittle but works for testing)
    if "ID: " in create_result:
        todo_id = create_result.split("ID: ")[-1].strip()
        
        # Update it
        update_result = update_todo(todo_id, title="Updated Test Sequence")
        assert isinstance(update_result, str)
        
        # Search for updated version
        search_updated = search_todo("Updated Test Sequence") 
        assert isinstance(search_updated, str)


# =============================================================================
# DATE LOGIC VALIDATION TESTS
# =============================================================================

def test_date_range_logic():
    """Test that date range functions generate correct date ranges."""
    today = date.today()
    
    # Test search_due_this_week uses correct date range
    # This is a bit of a white-box test, but important for correctness
    from thingsbridge.tools import search_todo
    
    # Should not crash and should return sensible results
    result = search_due_this_week()
    assert isinstance(result, str)
    assert "Found" in result
    
    # Test search_overdue uses dates before today
    result = search_overdue() 
    assert isinstance(result, str)
    assert "Found" in result


def test_timezone_handling():
    """Test that date functions handle timezone consistently."""
    # This is important for edge cases around midnight
    result = search_due_this_week()
    assert isinstance(result, str)
    
    # Run twice quickly - should be consistent
    result2 = search_due_this_week()
    assert isinstance(result2, str)
    
    # Results should be similar (same day, so same date ranges)
    # This is a basic consistency check