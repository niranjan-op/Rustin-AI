import json
import time

from langchain_core.messages import AIMessage, HumanMessage

from memory import add_to_long_term_memory
from models import fast_llm as fast_llm_model
from prompts import fast_llm_prompt
from states import AgentState
from tools import search_db


async def fast_llm_node(state: AgentState):
    print("running fast llm first")
    chain = fast_llm_prompt | fast_llm_model
    user_query = state.get("user_request", "")
    messages = state.get("messages", [])
    result = await chain.ainvoke(
        {"user_query": user_query,
        "messages": messages}
    )
    return {
        "messages": [result],
        "response": result.content
    }