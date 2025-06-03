# src/search_utils.py

import asyncio # For asyncio.to_thread
from duckduckgo_search import DDGS
from typing import List, Dict, Optional # Added Optional
from pydantic import ValidationError # For handling Pydantic errors

# Conceptual: Import API key from config.
# Although DDGS().text might not require it, other features or engines might.
from config import DUCKDUCKGO_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY # Ensure config loading
from utils.models import SearchResultItem # Added import

async def perform_duckduckgo_search(query: str, max_results: int = 5) -> List[SearchResultItem]:
    """
    Performs an asynchronous web search using DuckDuckGo (via asyncio.to_thread) 
    and returns a list of SearchResultItem objects.

    Args:
        query: The search query string.
        max_results: The maximum number of results to return.

    Returns:
        A list of SearchResultItem objects.
        Returns an empty list if an error occurs or no valid results are found.
    """
    parsed_results: List[SearchResultItem] = []
    
    # Conceptual: Placeholder for using DUCKDUCKGO_API_KEY if the library/feature required it
    # if not DUCKDUCKGO_API_KEY:
    #     print("Error: DuckDuckGo API key is not set.")
    #     return results
    # ddgs_instance = DDGS(headers={'x-api-key': DUCKDUCKGO_API_KEY}) # Example if key was needed for DDGS object

    ddgs = DDGS() # Instantiate DDGS

    try:
        print(f"Performing asynchronous DuckDuckGo search (via to_thread) for: '{query}' with max_results={max_results}")
        raw_results = await asyncio.to_thread(ddgs.text, keywords=query, max_results=max_results)
        
        if raw_results:
            for res_dict in raw_results:
                try:
                    link_url = res_dict.get('href')
                    if not link_url:
                        print(f"[perform_duckduckgo_search] Warning: Result missing 'href'. Skipping: {res_dict.get('title')}")
                        continue

                    search_item = SearchResultItem(
                        title=res_dict.get('title', 'No Title Provided'),
                        link=link_url, 
                        snippet=res_dict.get('body'), # 'body' from DDGS maps to 'snippet'
                        source_api="duckduckgo",
                        content=None, # DDGS text search doesn't provide full page content
                        raw_result=dict(res_dict) 
                    )
                    parsed_results.append(search_item)
                except ValidationError as ve:
                    print(f"[perform_duckduckgo_search] Pydantic validation error for result: {res_dict}. Error: {ve}. Skipping.")
                except Exception as e: 
                    print(f"[perform_duckduckgo_search] Error parsing result: {res_dict}. Error: {e}. Skipping.")
        else:
            print("No results returned from ddgs.text via to_thread")
            
    except Exception as e:
        print(f"Error during asynchronous DuckDuckGo search (via to_thread): {e}")
        # parsed_results will remain an empty list
    
    return parsed_results

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
    search_results_items = asyncio.run(perform_duckduckgo_search(query=sample_query, max_results=3)) 
    
    if search_results_items:
        print(f"\nFound {len(search_results_items)} results (async to_thread):")
        for i, item in enumerate(search_results_items, 1):
            print(f"\nResult {i} (SearchResultItem):")
            print(item.model_dump_json(indent=2))
            # Or print specific fields:
            # print(f"  Title: {item.title}")
            # print(f"  URL: {item.link}")
            # print(f"  Snippet: {item.snippet}")
            # print(f"  Source: {item.source_api}")
    else:
        print("No search results found or an error occurred.")

    print("\nsearch_utils.py test finished.")
