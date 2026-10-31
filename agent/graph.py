from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agent.nodes import memory_update_node, orchestrator_llm_node, thinking_node, coder_thinking_node, coding_node, research_node
from agent.states import AgentState
from tools import coding_tools, non_coding_tools

# 1. Initialize the state graph
workflow = StateGraph(AgentState)

# 2. Register LLM nodes
workflow.add_node("orchestrator_llm", orchestrator_llm_node)
workflow.add_node("thinking_node", thinking_node)
workflow.add_node("coder_thinking_node", coder_thinking_node)
workflow.add_node("coding_node", coding_node)
workflow.add_node("research_node", research_node)

# 3. Register Tool nodes
all_tools = coding_tools + non_coding_tools
workflow.add_node("orchestrator_tools", ToolNode(all_tools))
workflow.add_node("thinking_tools_node", ToolNode(all_tools))
workflow.add_node("coder_thinking_tools_node", ToolNode(all_tools))
workflow.add_node("coding_tools_node", ToolNode(all_tools))
workflow.add_node("research_tools_node", ToolNode(all_tools))
workflow.add_node("memory_update_node", memory_update_node)

# 4. Define custom routers
def route_from_memory(state: AgentState):
    """Router to direct traffic when resuming or starting based on active phase"""
    phase = state.get("current_phase")
    if phase == "thinking":
        return "thinking_node"
    elif phase == "coder_thinking":
        return "coder_thinking_node"
    elif phase == "coding":
        return "coding_node"
    elif phase == "research":
        return "research_node"
    return "orchestrator_llm"

def log_routing(msg):
    import os
    with open("router_debug.log", "a") as f:
        f.write(msg + "\n")

def route_from_orchestrator(state: AgentState):
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            log_routing(f"orchestrator_llm -> orchestrator_tools (phase={state.get('current_phase')})")
            return "orchestrator_tools"
            
    phase = state.get("current_phase")
    log_routing(f"orchestrator_llm -> {phase}_node (no tools)")
    if phase == "thinking":
        return "thinking_node"
    elif phase == "coder_thinking":
        return "coder_thinking_node"
    elif phase == "coding":
        return "coding_node"
    elif phase == "research":
        return "research_node"
    return END

def route_from_thinking(state: AgentState):
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            log_routing(f"thinking_node -> thinking_tools_node (phase={state.get('current_phase')})")
            return "thinking_tools_node"
            
    phase = state.get("current_phase")
    log_routing(f"thinking_node -> {phase}_node (no tools)")
    if phase == "coder_thinking":
        return "coder_thinking_node"
    elif phase == "coding":
        return "coding_node"
    elif phase == "orchestrating":
        return "orchestrator_llm"
    elif phase == "research":
        return "research_node"
    return END

def route_from_coder_thinking(state: AgentState):
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            log_routing(f"coder_thinking_node -> coder_thinking_tools_node (phase={state.get('current_phase')})")
            return "coder_thinking_tools_node"
            
    phase = state.get("current_phase")
    log_routing(f"coder_thinking_node -> {phase}_node (no tools)")
    if phase == "coding":
        return "coding_node"
    elif phase == "thinking":
        return "thinking_node"
    elif phase == "orchestrating":
        return "orchestrator_llm"
    return END

def route_from_coding(state: AgentState):
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            log_routing(f"coding_node -> coding_tools_node (phase={state.get('current_phase')})")
            return "coding_tools_node"
            
    phase = state.get("current_phase")
    log_routing(f"coding_node -> {phase}_node (no tools)")
    if phase == "coder_thinking":
        return "coder_thinking_node"
    elif phase == "thinking":
        return "thinking_node"
    elif phase == "orchestrating":
        return "orchestrator_llm"
    elif phase == "research":
        return "research_node"
    return END

def route_from_research(state: AgentState):
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            log_routing(f"research_node -> research_tools_node (phase={state.get('current_phase')})")
            return "research_tools_node"
            
    phase = state.get("current_phase")
    log_routing(f"research_node -> {phase}_node (no tools)")
    if phase == "thinking":
        return "thinking_node"
    elif phase == "coder_thinking":
        return "coder_thinking_node"
    elif phase == "orchestrating":
        return "orchestrator_llm"
    return END

def route_after_orchestrator_tools(state: AgentState):
    phase = state.get("current_phase")
    log_routing(f"orchestrator_tools -> {phase}_node")
    if phase == "thinking":
        return "thinking_node"
    elif phase == "coder_thinking":
        return "coder_thinking_node"
    elif phase == "coding":
        return "coding_node"
    elif phase == "research":
        return "research_node"
    return "orchestrator_llm"

def route_after_thinking_tools(state: AgentState):
    phase = state.get("current_phase")
    log_routing(f"thinking_tools_node -> {phase}_node")
    if phase == "coder_thinking":
        return "coder_thinking_node"
    elif phase == "coding":
        return "coding_node"
    elif phase == "orchestrating":
        return "orchestrator_llm"
    return "thinking_node"

def route_after_coder_thinking_tools(state: AgentState):
    phase = state.get("current_phase")
    log_routing(f"coder_thinking_tools_node -> {phase}_node")
    if phase == "coding":
        return "coding_node"
    elif phase == "thinking":
        return "thinking_node"
    elif phase == "orchestrating":
        return "orchestrator_llm"
    return "coder_thinking_node"

def route_after_coding_tools(state: AgentState):
    phase = state.get("current_phase")
    log_routing(f"coding_tools_node -> {phase}_node")
    if phase == "coder_thinking":
        return "coder_thinking_node"
    elif phase == "thinking":
        return "thinking_node"
    elif phase == "orchestrating":
        return "orchestrator_llm"
    elif phase == "research":
        return "research_node"
    return "coding_node"

def route_after_research_tools(state: AgentState):
    phase = state.get("current_phase")
    log_routing(f"research_tools_node -> {phase}_node")
    if phase == "thinking":
        return "thinking_node"
    elif phase == "coder_thinking":
        return "coder_thinking_node"
    elif phase == "orchestrating":
        return "orchestrator_llm"
    return "research_node"

# 5. Define the flow edges
workflow.add_edge(START, "memory_update_node")
workflow.add_conditional_edges("memory_update_node", route_from_memory)

# Orchestrator Loop
workflow.add_conditional_edges("orchestrator_llm", route_from_orchestrator)
workflow.add_conditional_edges("orchestrator_tools", route_after_orchestrator_tools)

# Thinking Loop
workflow.add_conditional_edges("thinking_node", route_from_thinking)
workflow.add_conditional_edges("thinking_tools_node", route_after_thinking_tools)

# Coder Thinking Loop
workflow.add_conditional_edges("coder_thinking_node", route_from_coder_thinking)
workflow.add_conditional_edges("coder_thinking_tools_node", route_after_coder_thinking_tools)

# Coding Loop
workflow.add_conditional_edges("coding_node", route_from_coding)
workflow.add_conditional_edges("coding_tools_node", route_after_coding_tools)

# Research Loop
workflow.add_conditional_edges("research_node", route_from_research)
workflow.add_conditional_edges("research_tools_node", route_after_research_tools)

# 6. Compile the workflow
app_graph = workflow.compile()
