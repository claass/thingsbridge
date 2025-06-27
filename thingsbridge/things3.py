"""Things 3 AppleScript integration."""

import logging
from typing import Dict, List, Optional, Any
from .applescript import executor, AppleScriptResult

logger = logging.getLogger(__name__)

class ThingsError(Exception):
    """Base exception for Things 3 operations."""
    pass

class Things3Client:
    """Client for interacting with Things 3 via AppleScript."""
    
    def __init__(self):
        self.executor = executor
    
    def ensure_running(self) -> None:
        """Ensure Things 3 is running."""
        result = self.executor.ensure_things_running()
        if not result.success:
            raise ThingsError(f"Failed to launch Things 3: {result.error}")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Things 3."""
        script = '''
        tell application "Things3"
            return name
        end tell
        '''
        
        result = self.executor.execute(script)
        if not result.success:
            return {
                "connected": False,
                "error": result.error,
                "app_running": self.executor.check_things_running()
            }
        
        return {
            "connected": True,
            "app_name": result.output,
            "app_running": True
        }
    
    def get_version_info(self) -> Dict[str, str]:
        """Get Things 3 version information."""
        script = '''
        tell application "Things3"
            return version
        end tell
        '''
        
        result = self.executor.execute(script)
        if not result.success:
            raise ThingsError(f"Failed to get version: {result.error}")
        
        return {
            "version": result.output,
            "app_name": "Things 3"
        }
    
    def create_simple_todo(self, title: str, notes: str = "") -> str:
        """Create a simple todo and return its ID."""
        # Escape quotes in title and notes
        safe_title = title.replace('"', '\\"')
        safe_notes = notes.replace('"', '\\"')
        
        script = f'''
        tell application "Things3"
            set newToDo to make new to do with properties {{name:"{safe_title}", notes:"{safe_notes}"}}
            return id of newToDo
        end tell
        '''
        
        result = self.executor.execute(script)
        if not result.success:
            raise ThingsError(f"Failed to create todo: {result.error}")
        
        return result.output
    
    def get_inbox_count(self) -> int:
        """Get count of items in inbox."""
        script = '''
        tell application "Things3"
            return count of to dos of list "Inbox"
        end tell
        '''
        
        result = self.executor.execute(script)
        if not result.success:
            raise ThingsError(f"Failed to get inbox count: {result.error}")
        
        try:
            return int(result.output)
        except ValueError:
            raise ThingsError(f"Invalid inbox count format: {result.output}")

# Global client instance
client = Things3Client()