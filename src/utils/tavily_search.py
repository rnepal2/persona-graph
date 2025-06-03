import asyncio
from tavily import TavilyClient # Official Tavily client
from typing import List, Optional, Dict, Any
from utils.models import SearchResultItem
from config import TAVILY_API_KEY # Will be added to config later
from pydantic import ValidationError # For handling potential model validation errors

async def perform_tavily_search(query: str, max_results: int = 5) -> List[SearchResultItem]:
    """
    Performs a search using Tavily API and returns a list of SearchResultItem objects.
    Tavily can also include pre-scraped content.
    """
    print(f"[perform_tavily_search] Performing Tavily search for: {query}")
    if not TAVILY_API_KEY:
        print("[perform_tavily_search] Error: TAVILY_API_KEY not configured.")
        return []

    # TavilyClient takes api_key directly at initialization
    client = TavilyClient(api_key=TAVILY_API_KEY)
    parsed_results: List[SearchResultItem] = []

    try:
        # Use client.search for basic search, or client.get_search_context for more detail including content
        # For now, let's use .search and assume it might have 'content' in results,
        # or we might need to adjust if its structure is different.
        # The Tavily API documentation suggests 'include_answer' and 'include_raw_content' parameters.
        # Let's try to get basic results first and then see if content is included.
        # We can use `search_depth="advanced"` for potentially more content.
        raw_response = await client.search(
            query=query,
            search_depth="basic", # Can be "advanced"
            max_results=max_results,
            # include_answer=True, # May include a summarized answer
            # include_raw_content=True, # May include full raw content of pages
            # include_images=False,
        )
        
        # Tavily results are typically in a 'results' key, which is a list of dicts
        tavily_results = raw_response.get("results", [])
        print(f"[perform_tavily_search] Received {len(tavily_results)} results from Tavily.")

        for res_dict in tavily_results: # Tavily already respects max_results from its API call
            try:
                link_url = res_dict.get('url') # Tavily uses 'url' not 'link' or 'href'
                if not link_url:
                    print(f"[perform_tavily_search] Warning: Result missing 'url'. Skipping: {res_dict.get('title')}")
                    continue
                
                # Check if 'content' is directly in the result dictionary
                # Some Tavily search results might include content directly.
                page_content = res_dict.get('content') 

                search_item = SearchResultItem(
                    title=res_dict.get('title', 'No Title Provided'),
                    link=link_url, # type: ignore 
                    snippet=res_dict.get('snippet'), # Tavily might not always have a 'snippet' field.
                                                   # It has 'content' which might be more detailed.
                                                   # Let's use 'content' as snippet if 'snippet' is missing.
                                                   # Or use a specific field if Tavily has a direct equivalent.
                                                   # For now, let's assume 'content' is the primary source.
                    source_api="tavily",
                    content=page_content, # Store the pre-fetched content if available
                    raw_result=dict(res_dict)
                )
                # If snippet is None and content is available, use beginning of content as snippet
                if search_item.snippet is None and search_item.content:
                    search_item.snippet = search_item.content[:250] + "..." # Example snippet length

                parsed_results.append(search_item)
            except ValidationError as ve:
                print(f"[perform_tavily_search] Pydantic validation error for result: {res_dict}. Error: {ve}. Skipping.")
            except Exception as e:
                print(f"[perform_tavily_search] Error parsing Tavily result: {res_dict}. Error: {e}. Skipping.")
    
    except Exception as e:
        print(f"[perform_tavily_search] Error during Tavily API call: {e}")
        return []

    return parsed_results

if __name__ == '__main__':
    async def main():
        print("Testing Tavily Search Utility...")
        if not TAVILY_API_KEY:
             print("TAVILY_API_KEY not found in environment. Search will be skipped by the function.")
        
        sample_query = "What is LangGraph?"
        # To actually test, you'd need to set TAVILY_API_KEY in your .env for this to run.
        results = await perform_tavily_search(sample_query, max_results=3)
        if results:
            print(f"Found {len(results)} results for '{sample_query}':")
            for item in results:
                print(item.model_dump_json(indent=2))
        else:
            print(f"No results found or error occurred for '{sample_query}'. Check API key if testing.")

    asyncio.run(main())
