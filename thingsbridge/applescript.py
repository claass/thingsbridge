"""AppleScript execution utilities for Things 3 integration."""

import subprocess
import json
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AppleScriptResult:
    """Result from AppleScript execution."""
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0

class AppleScriptExecutor:
    """Handles AppleScript execution with error handling and logging."""
    
    def __init__(self):
        self.timeout = 30  # Default timeout in seconds
    
    def execute(self, script: str, timeout: Optional[int] = None) -> AppleScriptResult:
        """Execute AppleScript and return structured result."""
        try:
            logger.debug(f"Executing AppleScript: {script[:100]}...")
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout
            )
            
            success = result.returncode == 0
            output = result.stdout.strip()
            error = result.stderr.strip() if result.stderr else None
            
            if success:
                logger.debug(f"AppleScript succeeded: {output[:100]}...")
            else:
                logger.error(f"AppleScript failed: {error}")
            
            return AppleScriptResult(
                success=success,
                output=output,
                error=error,
                exit_code=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            logger.error(f"AppleScript timeout after {timeout or self.timeout}s")
            return AppleScriptResult(
                success=False,
                output="",
                error=f"Script execution timed out after {timeout or self.timeout} seconds",
                exit_code=-1
            )
        except Exception as e:
            logger.error(f"AppleScript execution error: {e}")
            return AppleScriptResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1
            )
    
    def check_things_running(self) -> bool:
        """Check if Things 3 is running."""
        script = '''
        tell application "System Events"
            return (name of processes) contains "Things3"
        end tell
        '''
        result = self.execute(script)
        return result.success and result.output.lower() == "true"
    
    def ensure_things_running(self) -> AppleScriptResult:
        """Ensure Things 3 is running, launch if needed."""
        if self.check_things_running():
            return AppleScriptResult(success=True, output="Things 3 already running")
        
        script = '''
        tell application "Things3"
            activate
        end tell
        return "Things 3 launched"
        '''
        return self.execute(script)

# Global executor instance
executor = AppleScriptExecutor()