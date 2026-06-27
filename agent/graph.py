from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agent.nodes import memory_update_node, orchestrator_llm_node, thinking_node, coding_node
from agent.states import AgentState
from tools import coding_tools, non_coding_tools

# 1. Initialize the state graph
workflow = StateGraph(AgentState)

# 2. Register LLM nodes
workflow.add_node("orchestrator_llm", orchestrator_llm_node)
workflow.add_node("thinking_node", thinking_node)
workflow.add_node("coding_node", coding_node)

# 3. Register Tool nodes
all_tools = coding_tools + non_coding_tools
workflow.add_node("orchestrator_tools", ToolNode(all_tools))
workflow.add_node("thinking_tools_node", ToolNode(all_tools))
workflow.add_node("coding_tools_node", ToolNode(all_tools))
workflow.add_node("memory_update_node", memory_update_node)

# 4. Define custom routers
def route_from_memory(state: AgentState):
    """Router to direct traffic when resuming or starting based on active phase"""
    phase = state.get("current_phase")
    if phase == "thinking":
        return "thinking_node"
    elif phase == "coding":
        return "coding_node"
    return "orchestrator_llm"

def route_from_orchestrator(state: AgentState):
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "orchestrator_tools"
            
    phase = state.get("current_phase")
    if phase == "thinking":
        return "thinking_node"
    elif phase == "coding":
        return "coding_node"
    return END

def route_from_thinking(state: AgentState):
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "thinking_tools_node"
            
    phase = state.get("current_phase")
    if phase == "coding":
        return "coding_node"
    elif phase == "orchestrating":
        return "orchestrator_llm"
    return END

def route_from_coding(state: AgentState):
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "coding_tools_node"
            
    phase = state.get("current_phase")
    if phase == "thinking":
        return "thinking_node"
    elif phase == "orchestrating":
        return "orchestrator_llm"
    return END

# 5. Define the flow edges
workflow.add_edge(START, "memory_update_node")
workflow.add_conditional_edges("memory_update_node", route_from_memory)

# Orchestrator Loop
workflow.add_conditional_edges("orchestrator_llm", route_from_orchestrator)
workflow.add_edge("orchestrator_tools", "orchestrator_llm")

# Thinking Loop
workflow.add_conditional_edges("thinking_node", route_from_thinking)
workflow.add_edge("thinking_tools_node", "thinking_node")

# Coding Loop
workflow.add_conditional_edges("coding_node", route_from_coding)
workflow.add_edge("coding_tools_node", "coding_node")

# 6. Compile the workflow
app_graph = workflow.compile()
