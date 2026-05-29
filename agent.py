from states import AgentState
from nodes import orchestrator_llm_node
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from tools import tools

# 1. Initialize the state graph using your typed AgentState
workflow = StateGraph(AgentState)

# 2. Register the orchestrator LLM node and tools node
workflow.add_node("orchestrator_llm", orchestrator_llm_node)
workflow.add_node("tools", ToolNode(tools))

# 3. Define the flow edges
workflow.add_edge(START, "orchestrator_llm")
workflow.add_conditional_edges("orchestrator_llm", tools_condition)
workflow.add_edge("tools", "orchestrator_llm")

# 4. Compile the workflow into a runnable graph
app_graph = workflow.compile()