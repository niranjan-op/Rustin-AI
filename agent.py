from langgraph.graph import StateGraph, START, END
from states import AgentState
from nodes import fast_llm_node

# 1. Initialize the state graph using your typed AgentState
workflow = StateGraph(AgentState)

# 2. Register the fast LLM node
workflow.add_node("fast_llm_node", fast_llm_node)

# 3. Define the flow edges
workflow.add_edge(START, "fast_llm_node")
workflow.add_edge("fast_llm_node", END)

# 4. Compile the workflow into a runnable graph
app_graph = workflow.compile()