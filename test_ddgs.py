import sys

from ddgs import DDGS


def test_search():
    query = " best practices for React 19"
    print(f"Testing DDGS web search with query: '{query}'...\n")
    try:
        with DDGS() as ddgs:
            # We are requesting up to 3 results to test
            results = list(ddgs.text(query, max_results=3))

            if not results:
                print("No results found.")
                return

            for i, result in enumerate(results, start=1):
                print(f"Result #{i}:")
                print(f"  Title: {result.get('title')}")
                print(f"  Link:  {result.get('href')}")
                print(f"  Body:  {result.get('body')}\n")

            print("DDGS search API test completed successfully!")

    except ImportError:
        print("Error: The 'ddgs' package is not installed.")
        print("Please install it using 'pip install ddgs'")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during the search: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_search()
