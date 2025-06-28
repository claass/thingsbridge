"""Pytest configuration and fixtures for test cleanup."""

import logging
import pytest
from .test_cleanup import cleanup_test_artifacts, TestCleanupTracker

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_session():
    """Session-level fixture that cleans up test artifacts after all tests."""
    # Setup: Initialize tracker
    tracker = TestCleanupTracker()
    logger.info("Test session starting - cleanup tracking initialized")
    
    yield  # Run all tests
    
    # Teardown: Clean up all artifacts
    logger.info("Test session ending - starting cleanup")
    cleanup_test_artifacts()


@pytest.fixture(scope="function")
def cleanup_tracker():
    """Function-level fixture providing access to the cleanup tracker."""
    return TestCleanupTracker()


def pytest_runtest_setup(item):
    """Called before each test runs."""
    logger.debug(f"Starting test: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """Called after each test completes."""
    logger.debug(f"Completed test: {item.name}")


def pytest_sessionstart(session):
    """Called at the start of the test session."""
    logger.info("=" * 60)
    logger.info("ThingsBridge Test Session Starting")
    logger.info("Test artifact cleanup is ENABLED")
    logger.info("=" * 60)


def pytest_sessionfinish(session, exitstatus):
    """Called at the end of the test session."""
    tracker = TestCleanupTracker()
    stats = tracker.get_cleanup_stats()
    total = sum(stats.values())
    
    logger.info("=" * 60)
    logger.info("ThingsBridge Test Session Complete")
    logger.info(f"Exit status: {exitstatus}")
    logger.info(f"Test artifacts cleaned: {total} items")
    logger.info("=" * 60)


# Configure logging for cleanup system
def pytest_configure(config):
    """Configure pytest and logging."""
    # Set up logging for the cleanup system
    cleanup_logger = logging.getLogger('test_cleanup')
    cleanup_logger.setLevel(logging.INFO)
    
    # Create console handler if not already present
    if not cleanup_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - CLEANUP - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        cleanup_logger.addHandler(handler)