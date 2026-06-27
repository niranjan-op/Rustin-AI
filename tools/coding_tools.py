import ollama
from langchain_core.tools import tool

from core.memory import query_long_term_memory

# from core.models import orchestrator_project_llm
from services.git_manager import GitManager


# @tool
async def search_db(query: str, k: int) -> str:
    """Search the long-term memory database for user preferences and technical context. Input format: query: str, k: int"""
    return await query_long_term_memory(query, k)


@tool
def git_init() -> str:
    """Initialize a new git repository."""
    repo_path = _update_active_project_path()
    git = GitManager(repo_path)
    return git.init()


@tool
def git_status() -> str:
    """Get repository status."""
    repo_path = _update_active_project_path()
    git = GitManager(repo_path)
    return git.status()


@tool
def git_add_and_commit(message: str) -> str:
    """
    Stage and commit all changes in the current project.
    Input format: message: str (e.g. 'Initial commit' or 'Fixed login bug')
    """
    repo_path = _update_active_project_path()
    git = GitManager(repo_path)
    return git.add_and_commit(message)


@tool
def git_log(max_entries: int = 10) -> str:
    """View the git commit history for the current project."""
    repo_path = _update_active_project_path()
    git = GitManager(repo_path)
    return git.log(max_entries)


@tool
def git_reset(commit_hash: str = "HEAD") -> str:
    """
    Revert the workspace to a previously committed version.
    Use 'HEAD' to discard uncommitted changes, or provide a specific commit hash.
    Input format: commit_hash: str
    """
    repo_path = _update_active_project_path()
    git = GitManager(repo_path)
    return git.reset(commit_hash)


@tool
def execute_command_terminal(command: str) -> str:
    """
    Execute a bash/shell command on the user's machine directly through a node server.
    Note: Strict security checks are enforced. Commands related to network discovery (e.g., ipconfig, ping, netsh),
    system shutdown (e.g., shutdown, reboot), and identity revealing (e.g., whoami, hostname, %USERNAME%)
    are strictly banned and will fail execution. This tool should only be used for safe coding-related activities
    like executing code, compiling, checking versions, or creating virtual environments.
    WARNING: On Windows, this runs via cmd.exe. Do NOT use pipe `|` or redirect `<` `>` characters in your python -c commands or strings, as cmd.exe will parse them and cause syntax errors. Create a python file using create_file_to_wkng_dir and execute it instead for complex scripts.
    """
    from sandbox import node_sandbox as sandbox_node

    _update_active_project_path()
    result = sandbox_node.node_instance.execute_command(command)
    return result or ""


def _update_active_project_path():
    import sqlite3
    import urllib.parse

    from chainlit.context import get_context

    from sandbox import node_sandbox as sandbox_node

    project_path = None
    project_id = None
    try:
        context = get_context()
        if context and context.session:
            headers = getattr(context.session, "client_headers", {})
            if not headers and hasattr(context.session, "env"):
                headers = context.session.env

            cookie_str = headers.get("cookie", headers.get("Cookie", ""))
            for cookie in cookie_str.split(";"):
                parts = cookie.strip().split("=")
                if len(parts) >= 2 and parts[0] == "active_project_path":
                    project_path = urllib.parse.unquote("=".join(parts[1:]))
                if len(parts) >= 2 and parts[0] == "active_project_id":
                    project_id = urllib.parse.unquote("=".join(parts[1:]))

            if (
                (not project_path or project_path == "undefined")
                and project_id
                and project_id != "__none__"
            ):
                conn = sqlite3.connect(".files/test.db")
                cursor = conn.cursor()
                cursor.execute("SELECT path FROM projects WHERE id = ?", (project_id,))
                row = cursor.fetchone()
                if row:
                    project_path = row[0]
                conn.close()
    except Exception as e:
        print(f"Error fetching path in tool: {e}")

    if (
        not project_path
        or project_path == "undefined"
        or project_path == "null"
        or project_path == "None"
    ):
        import os
        project_path = os.getcwd()

    sandbox_node.node_instance.project_path = project_path
    print(f"Updated sandbox project path to: {project_path}")
    return sandbox_node.node_instance.project_path


@tool
def stop_node_server() -> str:
    """
    Stops the Node.js terminal server. Use this tool when you have finished executing commands and setting up/testing the application, to clean up resources.
    """
    from sandbox import node_sandbox as sandbox_node

    sandbox_node.node_instance.shutdown()
    return "Node server stopped successfully."


@tool
def route_to_thinking(reason: str) -> str:
    """
    Call this tool when the user's request involves complex coding tasks that require planning and thinking.
    This will redirect the execution flow to the dedicated thinking and planning node.
    Input format: reason: str (brief reason for routing)
    """
    return "Redirecting to thinking node for plan generation."


@tool
def route_back_to_thinking(reason: str) -> str:
    """
    Use this tool to return to the thinking node if the current plan is flawed, needs revision, or if you encounter errors you cannot solve.
    Input format: reason: str (e.g. 'Encountered architectural flaw requiring a revised plan')
    """
    return f"Routing back to thinking node: {reason}"


@tool
def route_to_coding(reason: str) -> str:
    """
    Call this tool when the plan is finalized and you are ready to hand over execution to the coding node.
    Input format: reason: str (e.g. 'Plan finalized, ready for implementation')
    """
    return f"Routing to coding node: {reason}"


@tool
def create_file_to_wkng_dir(name: str, content: str) -> str:
    """
    Create a new file in the current project directory with the given content.
    Input format: name: str (e.g. 'script.py'), content: str (the code)
    """
    from sandbox import node_sandbox as sandbox_node

    path = _update_active_project_path()
    if not path:
        return "Error: No active project path."

    success = sandbox_node.node_instance.create_file_to_wkng_dir(path, content, name)
    if success is True:
        return f"Successfully created {name}"
    else:
        return f"Failed to create {name}. Error: {success}"


@tool
def append_file_to_wkng_dir(name: str, content: str) -> str:
    """
    Append text content to an existing file in the current project directory.
    Input format: name: str (e.g. 'script.py'), content: str (the code)
    """
    from sandbox import node_sandbox as sandbox_node

    path = _update_active_project_path()
    if not path:
        return "Error: No active project path."

    success = sandbox_node.node_instance.append_file_to_wkng_dir(path, content, name)
    if success is True:
        return f"Successfully appended to {name}"
    else:
        return f"Failed to append to {name}. Error: {success}"


@tool
def edit_file_in_wkng_dir(name: str, target_content: str, replacement_content: str) -> str:
    """
    Edit an existing file in the current project directory by replacing a specific block of text.
    Input format: name: str (e.g. 'script.py'), target_content: str (the exact text to replace), replacement_content: str (the new text)
    """
    from sandbox import node_sandbox as sandbox_node

    path = _update_active_project_path()
    if not path:
        return "Error: No active project path."

    success = sandbox_node.node_instance.edit_file_in_wkng_dir(path, name, target_content, replacement_content)
    if success is True:
        return f"Successfully edited {name}"
    else:
        return f"Failed to edit {name}. Error: {success}"


@tool
def write_project_memory(content: str) -> str:
    """Overwrite the .model/project_memory.md with updated project knowledge. This should contain: project overview, tech stack, directory structure with file explanations, architectural decisions, known issues.
    Input format: content: str (the full markdown content)"""
    from sandbox import node_sandbox as sandbox_node
    path = _update_active_project_path()
    if not path:
        return 'Error: No active project path.'
    success = sandbox_node.node_instance.write_model_file(path, 'project_memory.md', content)
    return 'Project memory updated.' if success is True else f'Failed: {success}'


@tool
def write_tasks(content: str) -> str:
    """Overwrite the .model/tasks.md with the current task list. Use markdown checkboxes: - [ ] for pending, - [x] for completed.
    Input format: content: str (the full markdown content)"""
    from sandbox import node_sandbox as sandbox_node
    path = _update_active_project_path()
    if not path:
        return 'Error: No active project path.'
    success = sandbox_node.node_instance.write_model_file(path, 'tasks.md', content)
    return 'Tasks updated.' if success is True else f'Failed: {success}'


@tool
def append_project_timeline(entry: str) -> str:
    """Append a new timestamped entry to .model/project_timeline.md. Include: what was done, outcome (success/failure), git commit hash if applicable.
    Input format: entry: str (the markdown entry to append)"""
    from sandbox import node_sandbox as sandbox_node
    import datetime
    path = _update_active_project_path()
    if not path:
        return 'Error: No active project path.'
    timestamped = f'\n## {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}\n{entry}\n'
    success = sandbox_node.node_instance.append_model_file(path, 'project_timeline.md', timestamped)
    return 'Timeline updated.' if success is True else f'Failed: {success}'


coding_tools = [
    execute_command_terminal,
    stop_node_server,
    create_file_to_wkng_dir,
    append_file_to_wkng_dir,
    git_init,
    git_add_and_commit,
    git_log,
    git_status,
    git_reset,
    route_to_thinking,
    route_back_to_thinking,
    route_to_coding,
    edit_file_in_wkng_dir,
    write_project_memory,
    write_tasks,
    append_project_timeline,
]
non_coding_tools = []
tools = coding_tools + non_coding_tools
