from langchain_core.tools import tool

from git_manager import GitManager
from memory import query_long_term_memory


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
    # """
    # Execute a bash/shell command inside a secure Docker sandbox container.
    # You can run python code here using: python -c "..." or by writing code to files and running them.
    # Input: a single bash command string.
    # """
    # return execute_command_in_sandbox(command)
    import sandbox_node

    _update_active_project_path()
    result = sandbox_node.node_instance.execute_command(command)
    return result or ""


def _update_active_project_path():
    import sqlite3
    import urllib.parse

    from chainlit.context import get_context

    import sandbox_node

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
        project_path
        and project_path != "undefined"
        and project_path != "null"
        and project_path != "None"
    ):
        sandbox_node.node_instance.project_path = project_path
        print(f"Updated sandbox project path to: {project_path}")
    return sandbox_node.node_instance.project_path


@tool
def stop_node_server() -> str:
    """
    Stops the Node.js terminal server. Use this tool when you have finished executing commands and setting up/testing the application, to clean up resources.
    """
    import sandbox_node

    sandbox_node.node_instance.shutdown()
    return "Node server stopped successfully."


@tool
def create_file_to_wkng_dir(name: str, content: str) -> str:
    """
    Create a new file in the current project directory with the given content.
    Input format: name: str (e.g. 'script.py'), content: str (the code)
    """
    import sandbox_node

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
    import sandbox_node

    path = _update_active_project_path()
    if not path:
        return "Error: No active project path."

    success = sandbox_node.node_instance.append_file_to_wkng_dir(path, content, name)
    if success is True:
        return f"Successfully appended to {name}"
    else:
        return f"Failed to append to {name}. Error: {success}"


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
]
non_coding_tools = []
tools = coding_tools + non_coding_tools
