import asyncio
from agent import app_graph

async def main():
    state = {
        "user_request": "Hello, how are you?",
        "messages": []
    }
    print("Invoking graph...")
    try:
        result = await app_graph.ainvoke(state)
        print("Success! Result:")
        print(result)
    except Exception as e:
        print("Error during invoke:")
        import traceback
        traceback.print_exc()

asyncio.run(main())
