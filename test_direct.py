from models import fast_llm
import asyncio

print("Base URL:", fast_llm.base_url)
print("Model:", fast_llm.model)

async def test_direct():
    print("Testing direct model call...")
    try:
        res = await fast_llm.ainvoke("hello")
        print("Success direct call:", res)
    except Exception as e:
        print("Failed direct call:", e)

asyncio.run(test_direct())
