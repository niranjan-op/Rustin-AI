import operator
from typing import Annotated, List, Literal, Optional, TypedDict
from langchain_core.messages import AnyMessage
from pydantic import BaseModel, Field


class AgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], operator.add]
    user_request: str
    learned_features: list
    user_intent: str
    intent_category: str
    enriched_prompt: str
    draft_plan: str
    next_agent: Literal["planner", "coder", "intuitive"]
    response: str
    gathered_info: list
    searched_for: list
    elements: list[dict]
    
