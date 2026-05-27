import asyncio
import ollama_manager as m
from agent import app_graph

async def main():
    print("Checking if Ollama is running...")
    port = m.is_ollama_running()
    print("Ollama port status:", port)
    
    # Wait a few extra seconds to ensure Ollama is fully initialized
    await asyncio.sleep(5)
    
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
