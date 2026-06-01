from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from nodes import orchestrator_llm_node
from states import AgentState
from tools import coding_tools, non_coding_tools

# 1. Initialize the state graph using your typed AgentState
workflow = StateGraph(AgentState)

# 2. Register the orchestrator LLM node and tools node
workflow.add_node("orchestrator_llm", orchestrator_llm_node)
# We combine all tools into a single ToolNode. The LLMs will only use what they are bound to.
all_tools = coding_tools + non_coding_tools
workflow.add_node("tools", ToolNode(all_tools))

# 3. Define the flow edges
workflow.add_edge(START, "orchestrator_llm")
workflow.add_conditional_edges("orchestrator_llm", tools_condition)
workflow.add_edge("tools", "orchestrator_llm")

# 4. Compile the workflow into a runnable graph
app_graph = workflow.compile()
