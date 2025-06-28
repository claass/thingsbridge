"""Test cleanup system to track and remove test artifacts."""

import json
import logging
import os
import tempfile
import threading
import time
from datetime import datetime
from typing import Dict, List, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class TestCleanupTracker:
    """Tracks test artifacts for cleanup after test runs."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.cleanup_log_file = Path(tempfile.gettempdir()) / "thingsbridge_test_cleanup.json"
        self.created_todos: Set[str] = set()
        self.created_projects: Set[str] = set() 
        self.created_tags: Set[str] = set()
        self.test_session_id = f"test_session_{int(time.time())}"
        self._load_existing_log()
        
        logger.info(f"Test cleanup tracker initialized. Session: {self.test_session_id}")
        logger.info(f"Cleanup log: {self.cleanup_log_file}")
    
    def _load_existing_log(self):
        """Load any existing cleanup log."""
        if self.cleanup_log_file.exists():
            try:
                with open(self.cleanup_log_file, 'r') as f:
                    data = json.load(f)
                    # Load previous sessions that might not have been cleaned up
                    for session_data in data.values():
                        self.created_todos.update(session_data.get('todos', []))
                        self.created_projects.update(session_data.get('projects', []))
                        self.created_tags.update(session_data.get('tags', []))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not load existing cleanup log: {e}")
    
    def _save_log(self):
        """Save current state to cleanup log."""
        try:
            data = {}
            if self.cleanup_log_file.exists():
                with open(self.cleanup_log_file, 'r') as f:
                    data = json.load(f)
            
            data[self.test_session_id] = {
                'timestamp': datetime.now().isoformat(),
                'todos': list(self.created_todos),
                'projects': list(self.created_projects),
                'tags': list(self.created_tags)
            }
            
            with open(self.cleanup_log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cleanup log: {e}")
    
    def track_todo(self, todo_id: str):
        """Track a created todo for cleanup."""
        if todo_id and todo_id.strip():
            self.created_todos.add(todo_id.strip())
            self._save_log()
            logger.debug(f"Tracking todo for cleanup: {todo_id}")
    
    def track_project(self, project_id: str):
        """Track a created project for cleanup."""
        if project_id and project_id.strip():
            self.created_projects.add(project_id.strip())
            self._save_log()
            logger.debug(f"Tracking project for cleanup: {project_id}")
    
    def track_tag(self, tag_name: str):
        """Track a created tag for cleanup."""
        if tag_name and tag_name.strip():
            self.created_tags.add(tag_name.strip())
            self._save_log()
            logger.debug(f"Tracking tag for cleanup: {tag_name}")
    
    def get_cleanup_stats(self) -> Dict[str, int]:
        """Get count of items to clean up."""
        return {
            'todos': len(self.created_todos),
            'projects': len(self.created_projects), 
            'tags': len(self.created_tags)
        }
    
    def clear_session(self):
        """Clear the current session tracking."""
        self.created_todos.clear()
        self.created_projects.clear()
        self.created_tags.clear()
        
        # Remove current session from log file
        try:
            if self.cleanup_log_file.exists():
                with open(self.cleanup_log_file, 'r') as f:
                    data = json.load(f)
                data.pop(self.test_session_id, None)
                with open(self.cleanup_log_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to clear session from log: {e}")


def cleanup_test_artifacts():
    """Clean up all tracked test artifacts."""
    tracker = TestCleanupTracker()
    
    try:
        from thingsbridge.tools import delete_todo, delete_project
        from thingsbridge.search_tools import search_todo
        
        cleanup_stats = tracker.get_cleanup_stats()
        total_items = sum(cleanup_stats.values())
        
        if total_items == 0:
            logger.info("No test artifacts to clean up.")
            return
        
        logger.info(f"Starting cleanup of {total_items} test artifacts...")
        logger.info(f"  - Todos: {cleanup_stats['todos']}")
        logger.info(f"  - Projects: {cleanup_stats['projects']}")
        logger.info(f"  - Tags: {cleanup_stats['tags']}")
        
        cleaned_count = 0
        failed_count = 0
        
        # Clean up todos
        for todo_id in list(tracker.created_todos):
            try:
                result = delete_todo(todo_id)
                if "🗑️ Deleted todo" in result:
                    cleaned_count += 1
                    logger.debug(f"Cleaned up todo: {todo_id}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to clean up todo {todo_id}: {result}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Error cleaning up todo {todo_id}: {e}")
        
        # Clean up projects  
        for project_id in list(tracker.created_projects):
            try:
                result = delete_project(project_id)
                if "🗑️ Deleted project" in result:
                    cleaned_count += 1
                    logger.debug(f"Cleaned up project: {project_id}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to clean up project {project_id}: {result}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Error cleaning up project {project_id}: {e}")
        
        # Tags are harder to delete via AppleScript, so we'll just log them
        if tracker.created_tags:
            logger.info(f"Note: {len(tracker.created_tags)} test tags were created but cannot be automatically deleted: {list(tracker.created_tags)}")
        
        logger.info(f"Cleanup complete: {cleaned_count} items cleaned, {failed_count} failed")
        
        # Clear the session after successful cleanup
        tracker.clear_session()
        
    except ImportError as e:
        logger.error(f"Could not import cleanup tools: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {e}")


def extract_id_from_create_result(result: str) -> str:
    """Extract ID from create_todo or create_project result."""
    if "ID: " in result:
        return result.split("ID: ")[-1].strip()
    return ""


# Global tracker instance
_cleanup_tracker = TestCleanupTracker()


def track_created_todo(result: str) -> str:
    """Track a todo creation result and return the result unchanged."""
    todo_id = extract_id_from_create_result(result)
    if todo_id:
        _cleanup_tracker.track_todo(todo_id)
    return result


def track_created_project(result: str) -> str:
    """Track a project creation result and return the result unchanged.""" 
    project_id = extract_id_from_create_result(result)
    if project_id:
        _cleanup_tracker.track_project(project_id)
    return result


def track_created_tag(tag_name: str) -> str:
    """Track a tag creation and return the tag name unchanged."""
    _cleanup_tracker.track_tag(tag_name)
    return tag_name