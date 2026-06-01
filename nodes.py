import json
import time
import chainlit as cl

from langchain_core.messages import AIMessage, HumanMessage

from memory import add_to_long_term_memory
from models import fast_llm, orchestrator_llm, orchestrator_project_llm
from prompts import (
    fast_llm_prompt,
    orchestrator_llm_prompt,
    orchestrator_project_llm_prompt,
)
from states import AgentState
from tools import search_db


async def fast_llm_node(state: AgentState):
    print("running fast llm first")
    chain = fast_llm_prompt | fast_llm
    user_query = state.get("user_request", "")
    messages = state.get("messages", [])
    result = await chain.ainvoke({"user_query": user_query, "messages": messages})
    return {"messages": [result], "response": result.content}


async def orchestrator_llm_node(state: AgentState):
    is_project = state.get("is_project", False)
    
    # Read terminal_access from Chainlit user session, default to True if not explicitly False
    terminal_access = True
    try:
        settings = cl.user_session.get("settings", {})
        terminal_access = settings.get("terminal_access", True)
    except Exception:
        pass

    if is_project and terminal_access:
        print("User inside project and terminal access is enabled!")
        print("Running orchestrator agent (access to terminal)")
        chain = orchestrator_project_llm_prompt | orchestrator_project_llm
        user_query = state.get("user_request", "")
        messages = state.get("messages", [])
        result = await chain.ainvoke({"user_query": user_query, "messages": messages})
        print(result)
    else:
        print("User outside project or terminal access disabled")
        chain = orchestrator_llm_prompt | orchestrator_llm
        user_query = state.get("user_request", "")
        messages = state.get("messages", [])
        result = await chain.ainvoke({"user_query": user_query, "messages": messages})
        print(result)
    return {"messages": [result], "response": result.content}
