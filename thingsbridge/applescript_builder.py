"""AppleScript generation utilities for Things 3 integration."""

from typing import Dict, List, Optional


def _sanitize_applescript_string(text: str) -> str:
    """Escape quotes and special characters for AppleScript."""
    if not text:
        return ""
    return text.replace('"', '\\"')


def build_todo_creation_script(
    properties: List[str], target_list: Optional[str] = None
) -> str:
    """
    Build AppleScript for creating a todo with given properties.

    Args:
        properties: List of property strings (e.g., 'name:"Todo Title"')
        target_list: Optional target list name

    Returns:
        Complete AppleScript string
    """
    properties_str = ", ".join(properties)

    if target_list:
        safe_list_name = _sanitize_applescript_string(target_list)
        return f"""
        tell application "Things3"
            set targetList to list "{safe_list_name}"
            set newToDo to make new to do at targetList with properties {{{properties_str}}}
            return id of newToDo
        end tell
        """
    else:
        return f"""
        tell application "Things3"
            set newToDo to make new to do with properties {{{properties_str}}}
            return id of newToDo
        end tell
        """


def build_project_creation_script(properties: List[str]) -> str:
    """
    Build AppleScript for creating a project with given properties.

    Args:
        properties: List of property strings

    Returns:
        Complete AppleScript string
    """
    properties_str = ", ".join(properties)

    return f"""
    tell application "Things3"
        set newProject to make new project with properties {{{properties_str}}}
        return id of newProject
    end tell
    """


def build_todo_update_script(todo_id: str, updates: List[str]) -> str:
    """
    Build AppleScript for updating a todo with given changes.

    Args:
        todo_id: The ID of the todo to update
        updates: List of update statements (e.g., 'set name of targetToDo to "New Name"')

    Returns:
        Complete AppleScript string
    """
    safe_id = _sanitize_applescript_string(todo_id)
    updates_str = "\n            ".join(updates)

    return f"""
    tell application "Things3"
        set targetToDo to to do id "{safe_id}"
        {updates_str}
        return name of targetToDo
    end tell
    """


def build_search_script(
    search_clause: str, limit: int = 10, safe_query: str = ""
) -> str:
    """
    Build AppleScript for searching todos with optional conditions.

    Args:
        search_clause: The search clause (e.g., "to dos whose name contains 'test'")
        limit: Maximum number of results
        safe_query: Safe query string for result message

    Returns:
        Complete AppleScript string
    """
    return f"""
    tell application "Things3"
        set searchResults to {search_clause}
        set resultCount to count of searchResults
        set resultText to "Found " & resultCount & " items matching '{safe_query}':\\n"
        
        repeat with i from 1 to (resultCount)
            if i > {limit} then exit repeat
            set currentToDo to item i of searchResults
            set todoId to id of currentToDo
            set todoName to name of currentToDo
            set todoNotes to notes of currentToDo
            set todoStatus to status of currentToDo
            set todoDueDate to due date of currentToDo
            set todoActivationDate to activation date of currentToDo
            
            set resultText to resultText & i & ". " & todoName & " (ID: " & todoId & ")"
            
            if todoStatus is not open then
                set resultText to resultText & " [" & todoStatus & "]"
            end if
            
            -- Add due date if present
            if todoDueDate is not missing value then
                set resultText to resultText & " | Due: " & (short date string of todoDueDate)
            end if
            
            -- Add activation date if present
            if todoActivationDate is not missing value then
                set resultText to resultText & " | Scheduled: " & (short date string of todoActivationDate)
            end if
            
            if todoNotes is not "" then
                set resultText to resultText & " - " & todoNotes
            end if
            set resultText to resultText & "\\n"
        end repeat
        
        return resultText
    end tell
    """


def build_list_script(list_name: str, list_title: str) -> str:
    """
    Build AppleScript for listing items from a specific list.

    Args:
        list_name: Name of the Things 3 list
        list_title: Display title for the results

    Returns:
        Complete AppleScript string
    """
    return f"""
    tell application "Things3"
        set listTodos to to dos of list "{list_name}"
        set taskCount to count of listTodos
        set resultText to "{list_title} (" & taskCount & " items):\\n\\n"
        
        repeat with i from 1 to taskCount
            set currentToDo to item i of listTodos
            set todoId to id of currentToDo
            set todoName to name of currentToDo
            set todoNotes to notes of currentToDo
            
            set resultText to resultText & "• " & todoName & " (ID: " & todoId & ")"
            if todoNotes is not "" then
                set resultText to resultText & " - " & todoNotes
            end if
            set resultText to resultText & "\\n"
        end repeat
        
        return resultText
    end tell
    """


def build_completion_script(todo_id: str) -> str:
    """
    Build AppleScript for completing a todo.

    Args:
        todo_id: The ID of the todo to complete

    Returns:
        Complete AppleScript string
    """
    safe_id = _sanitize_applescript_string(todo_id)

    return f"""
    tell application "Things3"
        set targetToDo to to do id "{safe_id}"
        set status of targetToDo to completed
        return name of targetToDo
    end tell
    """


def build_move_script(
    todo_id: str, destination_type: str, destination_name: str
) -> str:
    """
    Build AppleScript for moving a todo to a different location.

    Args:
        todo_id: The ID of the todo to move
        destination_type: Type of destination ("area", "project", "list")
        destination_name: Name of the destination

    Returns:
        Complete AppleScript string or error message
    """
    safe_id = _sanitize_applescript_string(todo_id)
    safe_destination = _sanitize_applescript_string(destination_name)

    if destination_type.lower() == "area":
        return f"""
        tell application "Things3"
            set targetToDo to to do id "{safe_id}"
            set targetArea to area "{safe_destination}"
            move targetToDo to targetArea
            return name of targetToDo
        end tell
        """
    elif destination_type.lower() == "project":
        return f"""
        tell application "Things3"
            set targetToDo to to do id "{safe_id}"
            set targetProject to project "{safe_destination}"
            set project of targetToDo to targetProject
            return name of targetToDo
        end tell
        """
    elif destination_type.lower() == "list":
        return f"""
        tell application "Things3"
            set targetToDo to to do id "{safe_id}"
            set targetList to list "{safe_destination}"
            move targetToDo to targetList
            return name of targetToDo
        end tell
        """
    else:
        return f"❌ Invalid destination type: {destination_type}. Use 'area', 'project', or 'list'"


def build_tag_addition_script(todo_id: str, tag_name: str) -> str:
    """
    Build AppleScript for adding a tag to a todo.

    Args:
        todo_id: The ID of the todo
        tag_name: Name of the tag to add

    Returns:
        Complete AppleScript string
    """
    safe_tag = _sanitize_applescript_string(tag_name)

    return f"""
    tell application "Things3"
        set targetToDo to to do id "{todo_id}"
        make new tag at targetToDo with properties {{name:"{safe_tag}"}}
    end tell
    """


def build_get_name_script(todo_id: str) -> str:
    """
    Build AppleScript for getting a todo's name.

    Args:
        todo_id: The ID of the todo

    Returns:
        Complete AppleScript string
    """
    safe_id = _sanitize_applescript_string(todo_id)

    return f"""
    tell application "Things3"
        return name of to do id "{safe_id}"
    end tell
    """


def build_move_to_list_script(todo_id: str, list_name: str) -> str:
    """
    Build AppleScript for moving a todo to a specific list.

    Args:
        todo_id: The ID of the todo
        list_name: Name of the target list

    Returns:
        Complete AppleScript string
    """
    safe_id = _sanitize_applescript_string(todo_id)
    safe_list = _sanitize_applescript_string(list_name)

    return f"""
    tell application "Things3"
        move to do id "{safe_id}" to list "{safe_list}"
    end tell
    """


# =============================================================================
# BATCH OPERATIONS - Native AppleScript batch processing
# =============================================================================


def build_batch_todo_creation_script(items: list) -> str:
    """
    Build AppleScript for creating multiple todos in a single execution.

    Args:
        items: List of dict items with 'title' and optional 'notes', 'when', 'deadline', 'tags', 'list_name'

    Returns:
        Complete AppleScript string that returns a list of created todo IDs
    """
    todo_commands = []

    for i, item in enumerate(items):
        title = _sanitize_applescript_string(item.get("title", ""))
        notes = _sanitize_applescript_string(item.get("notes", ""))

        properties = [f'name:"{title}"']
        if notes:
            properties.append(f'notes:"{notes}"')

        # Handle deadline
        deadline = item.get("deadline")
        if deadline:
            # Note: Date validation should be done before calling this function
            properties.append(f'due date:(date "{deadline}")')

        tags = item.get("tags")
        if tags:
            escaped_tags = [_sanitize_applescript_string(t) for t in tags]
            tag_list = "{" + ", ".join([f'"{t}"' for t in escaped_tags]) + "}"
            properties.append(f"tag names:{tag_list}")

        properties_str = ", ".join(properties)

        # Handle list assignment
        list_name = item.get("list_name")
        if list_name == "Someday" or (item.get("when", "").lower() == "someday"):
            target_list = "Someday"
        else:
            target_list = list_name

        if target_list:
            safe_list = _sanitize_applescript_string(target_list)
            todo_commands.append(
                f"""
            set targetList{i} to list "{safe_list}"
            set newToDo{i} to make new to do at targetList{i} with properties {{{properties_str}}}
            set todoId{i} to id of newToDo{i}"""
            )
        else:
            todo_commands.append(
                f"""
            set newToDo{i} to make new to do with properties {{{properties_str}}}
            set todoId{i} to id of newToDo{i}"""
            )

    # Build the result collection
    result_ids = [f"todoId{i}" for i in range(len(items))]
    result_list = "{" + ", ".join(result_ids) + "}"

    commands_str = "\\n            ".join(todo_commands)

    return f"""
    tell application "Things3"
        {commands_str}
        
        set resultIds to {result_list}
        set resultText to ""
        repeat with i from 1 to count of resultIds
            set resultText to resultText & item i of resultIds
            if i < count of resultIds then set resultText to resultText & ","
        end repeat
        return resultText
    end tell
    """


def build_batch_completion_script(todo_ids: list) -> str:
    """
    Build AppleScript for completing multiple todos in a single execution.

    Args:
        todo_ids: List of todo ID strings

    Returns:
        Complete AppleScript string that returns completed todo names
    """
    completion_commands = []

    for i, todo_id in enumerate(todo_ids):
        safe_id = _sanitize_applescript_string(todo_id)
        completion_commands.append(
            f"""
        set targetToDo{i} to to do id "{safe_id}"
        set todoName{i} to name of targetToDo{i}
        set status of targetToDo{i} to completed"""
        )

    # Build the result collection
    result_names = [f"todoName{i}" for i in range(len(todo_ids))]
    result_list = "{" + ", ".join(result_names) + "}"

    commands_str = "\\n            ".join(completion_commands)

    return f"""
    tell application "Things3"
        {commands_str}
        
        set resultNames to {result_list}
        set resultText to ""
        repeat with i from 1 to count of resultNames
            set resultText to resultText & item i of resultNames
            if i < count of resultNames then set resultText to resultText & "|"
        end repeat
        return resultText
    end tell
    """


def build_batch_update_script(updates: list) -> str:
    """
    Build AppleScript for updating multiple todos in a single execution.

    Args:
        updates: List of dict items with 'todo_id' and update fields

    Returns:
        Complete AppleScript string that returns updated todo names
    """
    update_commands = []

    for i, update in enumerate(updates):
        todo_id = _sanitize_applescript_string(update["todo_id"])
        update_commands.append(f'set targetToDo{i} to to do id "{todo_id}"')

        if "title" in update and update["title"]:
            title = _sanitize_applescript_string(update["title"])
            update_commands.append(f'set name of targetToDo{i} to "{title}"')

        if "notes" in update and update["notes"] is not None:
            notes = _sanitize_applescript_string(update["notes"]).replace("!", "\\\\!")
            update_commands.append(f'set notes of targetToDo{i} to "{notes}"')

        if "deadline" in update and update["deadline"]:
            # Note: Date validation should be done before calling this function
            deadline = update["deadline"]
            update_commands.append(
                f'set due date of targetToDo{i} to (date "{deadline}")'
            )

        update_commands.append(f"set todoName{i} to name of targetToDo{i}")

    # Build the result collection
    result_names = [f"todoName{i}" for i in range(len(updates))]
    result_list = "{" + ", ".join(result_names) + "}"

    commands_str = "\\n            ".join(update_commands)

    return f"""
    tell application "Things3"
        {commands_str}
        
        set resultNames to {result_list}
        set resultText to ""
        repeat with i from 1 to count of resultNames
            set resultText to resultText & item i of resultNames
            if i < count of resultNames then set resultText to resultText & "|"
        end repeat
        return resultText
    end tell
    """


def build_batch_move_script(moves: list) -> str:
    """
    Build AppleScript for moving multiple todos in a single execution.

    Args:
        moves: List of dict items with 'todo_id', 'destination_type', 'destination_name'

    Returns:
        Complete AppleScript string that returns moved todo names
    """
    move_commands = []

    for i, move in enumerate(moves):
        todo_id = _sanitize_applescript_string(move["todo_id"])
        dest_type = move["destination_type"].lower()
        dest_name = _sanitize_applescript_string(move["destination_name"])

        move_commands.append(f'set targetToDo{i} to to do id "{todo_id}"')

        if dest_type == "area":
            move_commands.append(f'set targetArea{i} to area "{dest_name}"')
            move_commands.append(f"move targetToDo{i} to targetArea{i}")
        elif dest_type == "project":
            move_commands.append(f'set targetProject{i} to project "{dest_name}"')
            move_commands.append(f"set project of targetToDo{i} to targetProject{i}")
        elif dest_type == "list":
            move_commands.append(f'set targetList{i} to list "{dest_name}"')
            move_commands.append(f"move targetToDo{i} to targetList{i}")

        move_commands.append(f"set todoName{i} to name of targetToDo{i}")

    # Build the result collection
    result_names = [f"todoName{i}" for i in range(len(moves))]
    result_list = "{" + ", ".join(result_names) + "}"

    commands_str = "\\n            ".join(move_commands)

    return f"""
    tell application "Things3"
        {commands_str}
        
        set resultNames to {result_list}
        set resultText to ""
        repeat with i from 1 to count of resultNames
            set resultText to resultText & item i of resultNames
            if i < count of resultNames then set resultText to resultText & "|"
        end repeat
        return resultText
    end tell
    """
