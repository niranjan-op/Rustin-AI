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
    return mask_paths(git.status())


@tool
def git_add_and_commit(message: str) -> str:
    """
    Stage and commit all changes in the current project.
    Input format: message: str (e.g. 'Initial commit' or 'Fixed login bug')
    """
    repo_path = _update_active_project_path()
    git = GitManager(repo_path)
    return mask_paths(git.add_and_commit(message))


@tool
def git_log(max_entries: int = 10) -> str:
    """View the git commit history for the current project."""
    repo_path = _update_active_project_path()
    git = GitManager(repo_path)
    return mask_paths(git.log(max_entries))


@tool
def git_reset(commit_hash: str = "HEAD") -> str:
    """
    Revert the workspace to a previously committed version.
    Use 'HEAD' to discard uncommitted changes, or provide a specific commit hash.
    Input format: commit_hash: str
    """
    repo_path = _update_active_project_path()
    git = GitManager(repo_path)
    return mask_paths(git.reset(commit_hash))


@tool
def execute_commands_terminal(commands: list[str]) -> str:
    """
    Execute a list of bash/shell commands sequentially on the user's machine directly through a node server.
    Note: Strict security checks are enforced. Commands related to network discovery (e.g., ipconfig, ping, netsh),
    system shutdown (e.g., shutdown, reboot), and identity revealing (e.g., whoami, hostname, %USERNAME%)
    are strictly banned and will fail execution. This tool should only be used for safe coding-related activities
    like executing code, compiling, checking versions, or creating virtual environments.
    WARNING: On Windows, this runs via cmd.exe. Do NOT use pipe `|` or redirect `<` `>` characters in your python -c commands or strings, as cmd.exe will parse them and cause syntax errors. Create a python file using create_file_to_wkng_dir and execute it instead for complex scripts.
    Pass a list of commands, and they will be executed one by one. If one fails, execution stops.
    """
    from sandbox import node_sandbox as sandbox_node

    _update_active_project_path()
    result = sandbox_node.node_instance.execute_commands(commands)
    return mask_paths(result or "")


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
        if hasattr(sandbox_node.node_instance, "project_path") and sandbox_node.node_instance.project_path:
            project_path = sandbox_node.node_instance.project_path
        else:
            import os
            project_path = os.getcwd()

    sandbox_node.node_instance.project_path = project_path
    print(f"Updated sandbox project path to: {project_path}")
    return sandbox_node.node_instance.project_path


def mask_paths(text: str) -> str:
    """Mask absolute project paths and user home paths in the given text for privacy."""
    if not text or not isinstance(text, str):
        return text
        
    path = _update_active_project_path()
    if path and path not in ("undefined", "null", "None"):
        # Replace Windows backslashes and POSIX forward slashes
        text = text.replace(path, "[PROJECT_ROOT]")
        text = text.replace(path.replace("\\\\", "/"), "[PROJECT_ROOT]")
        text = text.replace(path.replace("/", "\\\\"), "[PROJECT_ROOT]")
        
    import os
    home_dir = os.path.expanduser("~")
    if home_dir and len(home_dir) > 3: # Avoid masking something too short like 'C:\\'
        text = text.replace(home_dir, "[HOME]")
        text = text.replace(home_dir.replace("\\\\", "/"), "[HOME]")
        text = text.replace(home_dir.replace("/", "\\\\"), "[HOME]")
        
    return text


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
def route_to_coder_thinking(reason: str) -> str:
    """
    Call this tool when the high-level plan is ready and needs to be translated
    into a concrete, code-level implementation specification before coding begins.
    Also call this from the coding node when errors need root-cause analysis before fixing,
    or when the user reports a bug or requests a new task.
    Input format: reason: str (detailed reason for routing)
    """
    return f"Routing to coder thinking node: {reason}"


@tool
def route_to_research(reason: str) -> str:
    """
    Call this tool to route to the Research Agent for deep web research or codebase feasibility studies.
    Input format: reason: str (detailed reason and topic for research)
    """
    return f"Routing to research node: {reason}"


@tool
def route_to_orchestrator(reason: str) -> str:
    """
    Call this tool to route back to the Orchestrator Manager when research or tasks are fully complete.
    Input format: reason: str
    """
    return f"Routing to orchestrator node: {reason}"


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
    CRITICAL: target_content must EXACTLY match the file's current content, including whitespace and indentation.
    If this tool fails, DO NOT simply retry with the same arguments. Use read_file_content to check the exact current text and indentation before trying again.
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


@tool
def search_in_project(keyword: str, file_extension: str = "") -> str:
    """
    Search for a keyword across all files in the current project directory.
    Returns matching file names, line numbers, and line content.
    Use this tool to find specific code patterns, function definitions, variable names, or strings before editing.
    Input format: keyword: str (the text to search for), file_extension: str (optional, e.g. '.py', '.js', '.html' to filter by type)
    """
    import os
    from pathlib import Path

    path = _update_active_project_path()
    if not path:
        return 'Error: No active project path.'

    results = []
    skip_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', '.model', '.env'}
    max_results = 50

    for root, dirs, files in os.walk(path):
        # Skip hidden/build directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if file_extension and not fname.endswith(file_extension):
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, path)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if keyword.lower() in line.lower():
                            results.append(f"{rel_path}:{line_num}: {line.rstrip()}")
                            if len(results) >= max_results:
                                break
            except (PermissionError, OSError):
                continue
            if len(results) >= max_results:
                break
        if len(results) >= max_results:
            break

    if not results:
        return f"No matches found for '{keyword}'{' in *' + file_extension + ' files' if file_extension else ''}."
    header = f"Found {len(results)} match(es) for '{keyword}':\n"
    return header + "\n".join(results)


@tool
def read_file_content(name: str, start_line: int = 1, end_line: int = 0) -> str:
    """
    Read the content of a file in the current project directory.
    Use this to inspect existing code before editing it.
    Input format: name: str (relative path e.g. 'src/app.py'), start_line: int (1-indexed, default 1), end_line: int (0 means entire file)
    """
    from pathlib import Path

    path = _update_active_project_path()
    if not path:
        return 'Error: No active project path.'

    target = Path(path) / name
    if not target.exists():
        return f"Error: File '{name}' does not exist."
    try:
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        total = len(lines)
        if end_line <= 0:
            end_line = total
        start_line = max(1, start_line)
        end_line = min(total, end_line)
        selected = lines[start_line - 1:end_line]
        header = f"File: {name} (lines {start_line}-{end_line} of {total})\n"
        numbered = "".join(f"{i}: {line}" for i, line in enumerate(selected, start_line))
        return header + numbered
    except Exception as e:
        return f"Error reading file: {e}"


coding_tools = [
    execute_commands_terminal,
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
    route_to_coder_thinking,
    edit_file_in_wkng_dir,
    search_in_project,
    read_file_content,
    write_project_memory,
    write_tasks,
    append_project_timeline,
]
@tool
def web_search(queries: list[str]) -> str:
    """
    Search the web using DuckDuckGo. Pass 2-3 queries to gather enough info.
    Input format: queries: list[str] (list of search queries)
    """
    try:
        from ddgs import DDGS
        import concurrent.futures
        import json
        
        all_results = []
        
        def fetch_query(q):
            with DDGS() as ddgs:
                return list(ddgs.text(q, max_results=15))
                
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_query = {executor.submit(fetch_query, q): q for q in queries}
            for future in concurrent.futures.as_completed(future_to_query):
                res = future.result()
                if res:
                    for r in res:
                        if not any(existing.get("href") == r.get("href") for existing in all_results):
                            all_results.append({
                                "title": r.get("title", ""),
                                "snippet": r.get("body", ""),
                                "href": r.get("href", "")
                            })
        return json.dumps(all_results, indent=2)
    except ImportError:
        return "Error: ddgs package is not installed."
    except Exception as e:
        return f"Error during web search: {e}"

@tool
def curl_fetch(urls: list[str]) -> str:
    """
    Fetch full text content from a list of URLs.
    Input format: urls: list[str]
    """
    import requests
    from bs4 import BeautifulSoup
    import concurrent.futures
    import json
    
    results = {}
    
    def fetch_url(url):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator=' ', strip=True)
            return text[:20000]
        except Exception as e:
            return f"Failed to fetch: {e}"

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(fetch_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            results[url] = future.result()
            
    return json.dumps(results, indent=2)

non_coding_tools = [web_search, curl_fetch]
tools = coding_tools + non_coding_tools
