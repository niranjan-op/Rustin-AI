import operator
from typing import Annotated, List, Literal, Optional, TypedDict

from langchain_core.messages import AnyMessage
from pydantic import BaseModel, Field


class AgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], operator.add]
    user_request: str
    user_profile: str
    learned_features: list
    response: str
    elements: list[dict]
    is_project: bool
    project_id: Optional[str]
    projet_path: Optional[str]
    welcome_context: Optional[str]  # The selected welcome message shown to the user
    project_structure: Optional[str]
    plan_approved: bool
    current_phase: Optional[str]
    # .model/ folder context
    project_memory: Optional[str]           # Contents of .model/project_memory.md
    pending_tasks: Optional[str]            # Contents of .model/tasks.md
    project_timeline: Optional[str]         # Contents of .model/project_timeline.md
    project_learned_features: Optional[list]  # Project-scoped lessons (what failed/succeeded)

