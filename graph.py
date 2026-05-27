# agent.py
from states import AgentState
from nodes import fast_llm_node
from langgraph.graph import StateGraph, START, END

# Initialize the state graph
workflow = StateGraph(AgentState)

# Add the node
workflow.add_node("fast_llm", fast_llm_node)

# Connect edges (or conditional routes depending on your logic)
workflow.add_edge(START, "fast_llm")
workflow.add_edge("fast_llm", END)

# Compile the graph
app_graph = workflow.compile()