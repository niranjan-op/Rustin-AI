import httpx
import asyncio

async def main():
    print("Testing httpx AsyncClient...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags")
            print("Async client success:", resp.status_code)
    except Exception as e:
        print("Async client failed:", e)
        import traceback
        traceback.print_exc()

    print("\nTesting httpx Sync Client...")
    try:
        with httpx.Client() as client:
            resp = client.get("http://127.0.0.1:11434/api/tags")
            print("Sync client success:", resp.status_code)
    except Exception as e:
        print("Sync client failed:", e)

asyncio.run(main())
