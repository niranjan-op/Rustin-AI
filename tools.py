from langchain_core.tools import tool

from memory import query_long_term_memory
from sandbox import execute_command_in_sandbox, write_file_to_sandbox
from sandbox_node import Node


# @tool
async def search_db(query: str, k: int) -> str:
    """Search the long-term memory database for user preferences and technical context. Input format: query: str, k: int"""
    return await query_long_term_memory(query, k)


@tool
def execute_code_sandbox(command: str) -> str:
    """
    Execute a bash/shell command on the user's machine directly through a node server.
    Note: Strict security checks are enforced. Commands related to network discovery (e.g., ipconfig, ping, netsh),
    system shutdown (e.g., shutdown, reboot), and identity revealing (e.g., whoami, hostname, %USERNAME%)
    are strictly banned and will fail execution. This tool should only be used for safe coding-related activities 
    like executing code, compiling, checking versions, or creating virtual environments.
    """
    # """
    # Execute a bash/shell command inside a secure Docker sandbox container.
    # You can run python code here using: python -c "..." or by writing code to files and running them.
    # Input: a single bash command string.
    # """
    # return execute_command_in_sandbox(command)
    node = Node()
    result = node.execute_command(command)
    return result or ""


@tool
def write_file_sandbox(file_path: str, content: str) -> str:
    """
    Write text content to a file inside the secure Docker sandbox container.
    Use this to save python scripts, bash scripts, or other files before executing them.
    Input format: file_path: str (e.g. 'script.py'), content: str (the code)
    """
    return write_file_to_sandbox(file_path, content)


tools = [execute_code_sandbox, write_file_sandbox]
