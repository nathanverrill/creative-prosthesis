import os
from langchain_community.utilities import SerpAPIWrapper
import asyncio # Import asyncio

# Initialize search wrapper once
search_wrapper = SerpAPIWrapper()

async def get_f1_results_async(): # Rename to indicate async
    """Searches for the latest F1 race results asynchronously."""
    print("--- Running Tool (Async): get_f1_results ---")
    try:
        # Use the async run method
        results = await search_wrapper.arun("latest F1 Grand Prix results summary standings key moments")
        return results
    except Exception as e:
        print(f"Error fetching F1 results async: {e}")
        return "Error: Could not fetch F1 results async."

# Keep the synchronous version if needed elsewhere, or remove it
def get_f1_results_sync():
    """Synchronous version for potential non-async use cases."""
    print("--- Running Tool (Sync): get_f1_results ---")
    try:
        results = search_wrapper.run("latest F1 Grand Prix results summary standings key moments")
        return results
    except Exception as e:
        print(f"Error fetching F1 results sync: {e}")
        return "Error: Could not fetch F1 results sync."

# --- Test function (optional) ---
async def test_async_search():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../../.env') # Adjust path
    print("Testing Async F1 Search...")
    info = await get_f1_results_async()
    print("Results snippet:", info[:200])

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(test_async_search())