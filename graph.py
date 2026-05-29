# agent.py
from states import AgentState
from nodes import fast_llm_node, orchestrator_llm_node
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from tools import tools

# Initialize the state graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("orchestrator_llm", orchestrator_llm_node)
workflow.add_node("tools", ToolNode(tools))

# Connect edges
workflow.add_edge(START, "orchestrator_llm")
workflow.add_conditional_edges("orchestrator_llm", tools_condition)
workflow.add_edge("tools", "orchestrator_llm")

# Compile the graph
app_graph = workflow.compile()