import asyncio
from agent import app_graph

async def main():
    state = {
        "user_request": "Hello, how are you?",
        "messages": []
    }
    print("Streaming events...")
    try:
        async for event in app_graph.astream_events(state, version="v2"):
            kind = event.get("event")
            name = event.get("name")
            print(f"Event: {kind}, Name: {name}")
            if kind == "on_chat_model_stream":
                content = event.get("data", {}).get("chunk", {}).content
                print(f"  Stream content: {repr(content)}")
            elif kind == "on_chain_end":
                output = event.get("data", {}).get("output")
                print(f"  Chain end output keys: {list(output.keys()) if isinstance(output, dict) else type(output)}")
    except Exception as e:
        print("Error during streaming:")
        import traceback
        traceback.print_exc()

asyncio.run(main())
