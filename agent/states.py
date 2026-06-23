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
    response: str
    gathered_info: list
    searched_for: list
    elements: list[dict]
    is_project: bool
    project_id: Optional[str]
    projet_path: Optional[str]
