import asyncio
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agent.graph import app_graph
from agent.states import AgentState

async def test_flow():
    state = {
        "messages": [
            HumanMessage(content="I want to create the famous missionary and monsters game. How should I proceed?"),
            AIMessage(content="I have created the plan. Do you approve?"),
            HumanMessage(content="Yes, go ahead and implement it.")
        ],
        "user_request": "Yes, go ahead and implement it.",
        "is_project": True,
        "project_id": "test_id",
        "current_phase": "thinking"
    }

    print("Starting graph...")
    try:
        async for event in app_graph.astream_events(state, config={"recursion_limit": 50}, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                node_name = event.get("metadata", {}).get("langgraph_node", "")
                if hasattr(chunk, "content") and chunk.content:
                    print(f"[{node_name}] {chunk.content}", end="", flush=True)
            elif kind == "on_chain_end":
                node = event.get("metadata", {}).get("langgraph_node")
                if node == "__start__":
                    print(f"\n[Graph finished: keys={event.get('data', {}).get('output', {}).keys()}]")
                elif not node:
                    print(f"\n[Graph output: {event.get('data', {}).get('output', {}).keys()}]")
                else:
                    print(f"\n[Node finished: {node}]")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(test_flow())
