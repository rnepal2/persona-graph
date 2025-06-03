import asyncio
from serpapi import SerpApiClient # Official SerpApi client
from typing import List, Optional, Dict, Any
from utils.models import SearchResultItem
from config import SERPAPI_API_KEY # Will be added to config later
from pydantic import ValidationError # For handling Pydantic errors

async def perform_serpapi_search(query: str, max_results: int = 5) -> List[SearchResultItem]:
    """
    Performs a search using SerpApi and returns a list of SearchResultItem objects.
    Note: The SerpApiClient is synchronous, so we run it in a thread.
    """
    print(f"[perform_serpapi_search] Performing SerpApi search for: {query}")
    if not SERPAPI_API_KEY:
        print("[perform_serpapi_search] Error: SERPAPI_API_KEY not configured.")
        return []

    client_params = {
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": max_results,  # Corresponds to 'num' parameter for number of results
        "engine": "google" # Default to Google, can be parameterized later
    }
    # client = SerpApiClient(client_params) # This is incorrect, SerpApiClient takes api_key as a top-level arg
                                        # and other params in get_dict() or get_json()

    parsed_results: List[SearchResultItem] = []
    try:
        # Corrected client initialization and call:
        # The SerpApiClient itself doesn't take all params at init for a search.
        # It takes the api_key. Search parameters go into the get_dict method.
        # However, the library's typical usage pattern is to pass all params to the search method.
        # Let's re-check library docs or assume the common pattern for such client libraries.
        # The example from SerpApi Python library:
        # client = GoogleSearch({ "q": "coffee", "api_key": "..."}) -> This is for GoogleSearch, not SerpApiClient
        # For SerpApiClient, it's:
        # client = SerpApiClient({"q": query, "engine": "google", ..., "api_key": SERPAPI_API_KEY})
        # So the original client_params was mostly correct but the client init was wrong.
        # Let's stick to the pattern where client takes all search params.
        
        # The SerpApiClient from `serpapi` library is a bit unusual.
        # The constructor `SerpApiClient(params_dict)` takes a dictionary of all parameters.
        # So, `client_params` including `api_key` is correct for the constructor.
        
        search = SerpApiClient(client_params)

        # SerpApiClient.get_dict() is synchronous
        raw_response = await asyncio.to_thread(search.get_dict)
        
        organic_results = raw_response.get("organic_results", [])
        
        print(f"[perform_serpapi_search] Received {len(organic_results)} results from SerpApi.")

        for res_dict in organic_results[:max_results]: # Ensure we respect max_results
            try:
                link_url = res_dict.get('link')
                if not link_url:
                    print(f"[perform_serpapi_search] Warning: Result missing 'link'. Skipping: {res_dict.get('title')}")
                    continue

                search_item = SearchResultItem(
                    title=res_dict.get('title', 'No Title Provided'),
                    link=link_url, 
                    snippet=res_dict.get('snippet'),
                    source_api="serpapi",
                    raw_result=dict(res_dict)
                )
                parsed_results.append(search_item)
            except ValidationError as ve:
                print(f"[perform_serpapi_search] Pydantic validation error for result: {res_dict}. Error: {ve}. Skipping.")
            except Exception as e:
                print(f"[perform_serpapi_search] Error parsing SerpApi result: {res_dict}. Error: {e}. Skipping.")
    
    except Exception as e:
        print(f"[perform_serpapi_search] Error during SerpApi call: {e}")
        return [] # Return empty list on error

    return parsed_results

if __name__ == '__main__':
    async def main():
        print("Testing SerpApi Search Utility...")
        # Ensure SERPAPI_API_KEY is loaded via config if you run this directly for testing
        # For this example, we'll rely on it being None and printing the error.
        if not SERPAPI_API_KEY:
             print("SERPAPI_API_KEY not found in environment. Search will be skipped by the function.")
        
        sample_query = "latest advancements in AI"
        # To actually test, you'd need to set SERPAPI_API_KEY in your .env for this to run.
        # The function perform_serpapi_search will print an error and return [] if key is missing.
        results = await perform_serpapi_search(sample_query, max_results=3)
        if results:
            print(f"Found {len(results)} results for '{sample_query}':")
            for item in results:
                print(item.model_dump_json(indent=2))
        else:
            print(f"No results found or error occurred for '{sample_query}'. Check API key if testing.")

    asyncio.run(main())
