from langchain_core.tools import tool
from memory import query_long_term_memory

@tool
async def search_db(query: str, k: int) -> str:
    """Search the long-term memory database for user preferences and technical context. Input format: query: str, k: int"""
    return await query_long_term_memory(query, k)

tools = [search_db]
