import asyncio
from serpapi import SerpApiClient
from typing import List
from utils.models import SearchResultItem
from utils.config import config
from pydantic import ValidationError

async def perform_serpapi_search(query: str, max_results: int = None) -> List[SearchResultItem]:
    if not config.serpapi_api_key:
        return []
        
    if max_results is None:
        max_results = config.search.max_results

    client_params = {
        "q": query,
        "api_key": config.serpapi_api_key,
        "num": max_results,
        "engine": "google"
    }

    parsed_results: List[SearchResultItem] = []
    try:
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
        if not config.serpapi_api_key:
            print("SerpApi API key not found in config. Search will be skipped.")
        
        sample_query = "latest advancements in AI"
        results = await perform_serpapi_search(sample_query, max_results=3)
        if results:
            print(f"Found {len(results)} results for '{sample_query}':")
            for item in results:
                print(item.model_dump_json(indent=2))
        else:
            print(f"No results found or error occurred for '{sample_query}'. Check API key if testing.")

    asyncio.run(main())
