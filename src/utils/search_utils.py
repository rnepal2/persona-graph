# src/search_utils.py

import asyncio # For asyncio.to_thread
from duckduckgo_search import DDGS
from typing import List, Dict

# Conceptual: Import API key from config.
# Although DDGS().text might not require it, other features or engines might.
from src.config import DUCKDUCKGO_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY # Ensure config loading

async def perform_duckduckgo_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Performs an asynchronous web search using DuckDuckGo (via asyncio.to_thread) 
    and returns a list of results.

    Args:
        query: The search query string.
        max_results: The maximum number of results to return.

    Returns:
        A list of dictionaries, where each dictionary contains 'title', 'href', and 'body' of a search result.
        Returns an empty list if an error occurs.
    """
    results: List[Dict[str, str]] = []
    
    # Conceptual: Placeholder for using DUCKDUCKGO_API_KEY if the library/feature required it
    # if not DUCKDUCKGO_API_KEY:
    #     print("Error: DuckDuckGo API key is not set.")
    #     return results
    # ddgs_instance = DDGS(headers={'x-api-key': DUCKDUCKGO_API_KEY}) # Example if key was needed for DDGS object

    ddgs = DDGS() # Instantiate DDGS

    try:
        print(f"Performing asynchronous DuckDuckGo search (via to_thread) for: '{query}' with max_results={max_results}")
        # Wrap the synchronous ddgs.text() call in asyncio.to_thread
        # Note: DDGS().text() returns a generator, so the list conversion is important if that's what's expected.
        # However, the original code iterated over ddgs_results directly.
        # If ddgs.text is a generator, to_thread will run the generator to completion in the thread.
        # The result `raw_results` here would be the list if the generator is exhausted by `text` itself,
        # or it would be the generator object if `text` just returns it.
        # The `duckduckgo_search` library's `text` method actually returns a list directly when max_results is set.
        raw_results = await asyncio.to_thread(ddgs.text, keywords=query, max_results=max_results)
        
        if raw_results:
            for result in raw_results:
                # Ensure result is a dictionary and has the expected keys
                if isinstance(result, dict) and all(k in result for k in ['title', 'href', 'body']):
                    results.append({
                        'title': result['title'],
                        'href': result['href'],
                        'body': result['body']
                    })
                else:
                    print(f"Warning: Skipping malformed search result: {result}")
        else:
            print("No results returned from ddgs.text via to_thread")
            
    except Exception as e:
        print(f"Error during asynchronous DuckDuckGo search (via to_thread): {e}")
        # results will remain an empty list
    
    return results

if __name__ == "__main__":
    print("Testing search_utils.py (async with to_thread)...")

    # This demonstrates that API keys can be loaded from config.py
    print(f"Attempting to load API keys from src.config:")
    print(f"  OPENAI_API_KEY loaded: {'Yes' if OPENAI_API_KEY else 'No (or empty)'}")
    print(f"  GEMINI_API_KEY loaded: {'Yes' if GEMINI_API_KEY else 'No (or empty)'}")
    print(f"  DUCKDUCKGO_API_KEY loaded: {'Yes' if DUCKDUCKGO_API_KEY else 'No (or empty)'}")
    
    sample_query = "LangGraph use cases" # Using a consistent query
    print(f"\nPerforming search for query: '{sample_query}'")
    
    # Update to use asyncio.run for the async function
    search_results = asyncio.run(perform_duckduckgo_search(query=sample_query, max_results=3)) # Use specified max_results=3
    
    if search_results:
        print(f"\nFound {len(search_results)} results (async to_thread):")
        for i, res in enumerate(search_results, 1):
            print(f"\nResult {i}:")
            print(f"  Title: {res['title']}")
            print(f"  URL: {res['href']}")
            print(f"  Snippet: {res['body']}")
    else:
        print("No search results found or an error occurred.")

    print("\nsearch_utils.py test finished.")
