import asyncio
from tavily import TavilyClient
from typing import List
from utils.models import SearchResultItem
from utils.config import config
from pydantic import ValidationError

async def perform_tavily_search(query: str, max_results: int = None) -> List[SearchResultItem]:
    if not config.tavily_api_key:
        print("[perform_tavily_search] Error: Tavily API key not configured.")
        return []

    if max_results is None:
        max_results = config.search.max_results

    client = TavilyClient(api_key=config.tavily_api_key)
    parsed_results: List[SearchResultItem] = []

    try:
        raw_response = await client.search(
            query=query,
            search_depth="basic",
            max_results=max_results
        )
        
        # Tavily results are typically in a 'results' key, TODO: Check      
        tavily_results = raw_response.get("results", [])
        print(f"[perform_tavily_search] Received {len(tavily_results)} results from Tavily.")

        for res_dict in tavily_results:
            try:
                link_url = res_dict.get('url')
                if not link_url:
                    print(f"[perform_tavily_search] Warning: Result missing 'url'. Skipping: {res_dict.get('title')}")
                    continue
                
                page_content = res_dict.get('content')

                search_item = SearchResultItem(
                    title=res_dict.get('title', 'No Title Provided'),
                    link=link_url,
                    snippet=res_dict.get('snippet'),
                    source_api="tavily",
                    content=page_content,
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
        if not config.tavily_api_key:
            print("Tavily API key not found in config. Search will be skipped.")
        
        sample_query = "What is LangGraph?"
        results = await perform_tavily_search(sample_query, max_results=3)
        if results:
            print(f"Found {len(results)} results for '{sample_query}':")
            for item in results:
                print(item.model_dump_json(indent=2))
        else:
            print(f"No results found or error occurred for '{sample_query}'. Check API key if testing.")

    asyncio.run(main())
