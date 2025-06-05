# src/search_utils.py
import asyncio
from duckduckgo_search import DDGS
from typing import List, Dict, Optional 
from pydantic import ValidationError
from utils.models import SearchResultItem
from utils.config import DUCKDUCKGO_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY

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
    ddgs = DDGS()
    try:
        print(f"Async DuckDuckGo search (with to_thread)") 
        print(f"Query: {query}, max_results={max_results}")

        raw_results = await asyncio.to_thread(ddgs.text, keywords=query, max_results=max_results)
        if raw_results:
            for res_dict in raw_results:
                try:
                    link_url = res_dict.get('href')
                    if not link_url:
                        print(f"[duckduckgo_search] Warning: Result missing 'href'. Skipping: {res_dict.get('title')}")
                        continue

                    search_item = SearchResultItem(
                        title=res_dict.get('title', 'No Title Provided'),
                        link=link_url, 
                        snippet=res_dict.get('body'),
                        source_api="duckduckgo",
                        content=None, # DDGS text search doesn't provide full page content
                        raw_result=dict(res_dict) 
                    )
                    parsed_results.append(search_item)
                except ValidationError as ve:
                    print(f"[duckduckgo_search] Pydantic validation error for result: {res_dict}. Error: {ve}. Skipping.")
                except Exception as e: 
                    print(f"[duckduckgo_search] Error parsing result: {res_dict}. Error: {e}. Skipping.")
        else:
            print("No results returned from ddgs.text via to_thread")  
    except Exception as e:
        print(f"Error during asynchronous DuckDuckGo search (via to_thread): {e}")
    return parsed_results

if __name__ == "__main__":
    print("Testing search_utils.py (async with to_thread)...")    
    sample_query = "Who is Rabindra Nepal with PhD in Physics from University of Nebraska-Lincoln?"
    print(f"\nPerforming search for query: '{sample_query}'")
    search_results_items = asyncio.run(perform_duckduckgo_search(query=sample_query, max_results=5)) 
    if search_results_items:
        print(f"\nFound {len(search_results_items)} results (async to_thread):")
        for i, item in enumerate(search_results_items, 1):
            print(f"\nResult {i} (SearchResultItem):")
            print(item.model_dump_json(indent=2))
    else:
        print("No search results found or an error occurred.")
    print("\nsearch_utils.py test finished.")
