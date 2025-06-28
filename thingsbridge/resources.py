"""MCP resources for Things 3 integration."""

import logging
from typing import List, Dict, Any
from .things3 import client, ThingsError
from .cache import cached_resource

logger = logging.getLogger(__name__)

def _fetch_areas_uncached() -> List[Dict[str, Any]]:
    """Fetch areas from Things 3 without caching."""
    client.ensure_running()
    
    script = '''
    tell application "Things3"
        set allAreas to areas
        set areaCount to count of allAreas
        set jsonList to ""
        
        repeat with i from 1 to areaCount
            set currentArea to item i of allAreas
            set areaName to name of currentArea
            set areaId to id of currentArea
            
            if i > 1 then
                set jsonList to jsonList & ","
            end if
            
            set jsonList to jsonList & "{\\"name\\":\\"" & areaName & "\\",\\"id\\":\\"" & areaId & "\\"}"
        end repeat
        
        return "[" & jsonList & "]"
    end tell
    '''
    
    result = client.executor.execute(script)
    
    if not result.success:
        raise ThingsError(f"Failed to get areas: {result.error}")
    
    # Parse the JSON-like response
    import json
    try:
        areas_data = json.loads(result.output)
        return [{"name": area["name"], "id": area["id"], "type": "area"} for area in areas_data]
    except json.JSONDecodeError:
        logger.error(f"Failed to parse areas JSON: {result.output}")
        return []


@cached_resource("areas_list", ttl_seconds=300)  # 5 minutes
def areas_list() -> List[Dict[str, Any]]:
    """
    MCP resource providing list of available areas (cached for 5 minutes).
    
    Returns:
        List of area objects with name and metadata
    """
    try:
        logger.debug("Fetching areas list (cache miss or expired)")
        return _fetch_areas_uncached()
    except Exception as e:
        logger.error(f"Error getting areas resource: {e}")
        return []

def _fetch_projects_uncached() -> List[Dict[str, Any]]:
    """Fetch projects from Things 3 without caching."""
    client.ensure_running()
    
    script = '''
    tell application "Things3"
        set allProjects to projects
        set projectCount to count of allProjects
        set jsonList to ""
        
        repeat with i from 1 to projectCount
            set currentProject to item i of allProjects
            set projectName to name of currentProject
            set projectId to id of currentProject
            
            -- Get area name if project is in an area
            set areaName to ""
            try
                set projectArea to area of currentProject
                if projectArea is not missing value then
                    set areaName to name of projectArea
                end if
            end try
            
            if i > 1 then
                set jsonList to jsonList & ","
            end if
            
            set jsonList to jsonList & "{\\"name\\":\\"" & projectName & "\\",\\"id\\":\\"" & projectId & "\\",\\"area\\":\\"" & areaName & "\\"}"
        end repeat
        
        return "[" & jsonList & "]"
    end tell
    '''
    
    result = client.executor.execute(script)
    
    if not result.success:
        raise ThingsError(f"Failed to get projects: {result.error}")
    
    # Parse the JSON-like response
    import json
    try:
        projects_data = json.loads(result.output)
        return [{"name": proj["name"], "id": proj["id"], "area": proj["area"], "type": "project"} for proj in projects_data]
    except json.JSONDecodeError:
        logger.error(f"Failed to parse projects JSON: {result.output}")
        return []


@cached_resource("projects_list", ttl_seconds=300)  # 5 minutes
def projects_list() -> List[Dict[str, Any]]:
    """
    MCP resource providing list of available projects (cached for 5 minutes).
    
    Returns:
        List of project objects with name, area, and metadata
    """
    try:
        logger.debug("Fetching projects list (cache miss or expired)")
        return _fetch_projects_uncached()
    except Exception as e:
        logger.error(f"Error getting projects resource: {e}")
        return []

def today_tasks() -> List[Dict[str, Any]]:
    """
    MCP resource providing today's scheduled tasks.
    
    Returns:
        List of task objects for today
    """
    try:
        client.ensure_running()
        
        script = '''
        tell application "Things3"
            set todayTodos to to dos of list "Today"
            set taskCount to count of todayTodos
            set jsonList to ""
            
            repeat with i from 1 to taskCount
                set currentToDo to item i of todayTodos
                set todoName to name of currentToDo
                set todoId to id of currentToDo
                set todoNotes to notes of currentToDo
                
                if i > 1 then
                    set jsonList to jsonList & ","
                end if
                
                set jsonList to jsonList & "{\\"name\\":\\"" & todoName & "\\",\\"id\\":\\"" & todoId & "\\",\\"notes\\":\\"" & todoNotes & "\\"}"
            end repeat
            
            return "[" & jsonList & "]"
        end tell
        '''
        
        result = client.executor.execute(script)
        
        if not result.success:
            raise ThingsError(f"Failed to get today's tasks: {result.error}")
        
        # Parse the JSON-like response
        import json
        try:
            tasks_data = json.loads(result.output)
            return [{"name": task["name"], "id": task["id"], "notes": task["notes"], "type": "task"} for task in tasks_data]
        except json.JSONDecodeError:
            logger.error(f"Failed to parse today tasks JSON: {result.output}")
            return []
        
    except Exception as e:
        logger.error(f"Error getting today tasks resource: {e}")
        return []

def inbox_items() -> List[Dict[str, Any]]:
    """
    MCP resource providing inbox items.
    
    Returns:
        List of inbox task objects
    """
    try:
        client.ensure_running()
        
        script = '''
        tell application "Things3"
            set inboxTodos to to dos of list "Inbox"
            set taskCount to count of inboxTodos
            set jsonList to ""
            
            repeat with i from 1 to taskCount
                set currentToDo to item i of inboxTodos
                set todoName to name of currentToDo
                set todoId to id of currentToDo
                set todoNotes to notes of currentToDo
                
                if i > 1 then
                    set jsonList to jsonList & ","
                end if
                
                set jsonList to jsonList & "{\\"name\\":\\"" & todoName & "\\",\\"id\\":\\"" & todoId & "\\",\\"notes\\":\\"" & todoNotes & "\\"}"
            end repeat
            
            return "[" & jsonList & "]"
        end tell
        '''
        
        result = client.executor.execute(script)
        
        if not result.success:
            raise ThingsError(f"Failed to get inbox items: {result.error}")
        
        # Parse the JSON-like response
        import json
        try:
            items_data = json.loads(result.output)
            return [{"name": item["name"], "id": item["id"], "notes": item["notes"], "type": "task"} for item in items_data]
        except json.JSONDecodeError:
            logger.error(f"Failed to parse inbox items JSON: {result.output}")
            return []
        
    except Exception as e:
        logger.error(f"Error getting inbox items resource: {e}")
        return []