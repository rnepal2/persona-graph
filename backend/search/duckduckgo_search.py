import asyncio
from duckduckgo_search import DDGS
from typing import List
from pydantic import ValidationError
from utils.models import SearchResultItem
from utils.config import config

async def perform_duckduckgo_search(query: str, max_results: int = None) -> List[SearchResultItem]:
    if max_results is None:
        max_results = config.search.max_results
        
    parsed_results: List[SearchResultItem] = []
    try:
        print(f">>>[DuckDuckGo Search] Query: {query}")
        raw_results = await asyncio.to_thread(DDGS().text, keywords=query, max_results=max_results)
        
        if not raw_results:
            return []

        for res_dict in raw_results:
            try:
                link_url = res_dict.get('href')
                if not link_url:
                    continue

                parsed_results.append(SearchResultItem(
                    title=res_dict.get('title', 'No Title Provided'),
                    link=link_url,
                    snippet=res_dict.get('body'),
                    source_api="duckduckgo",
                    content=None,
                    raw_result=dict(res_dict)
                ))
            except (ValidationError, Exception) as e:
                print(f"[DDG] Error parsing result: {e}")
                
    except Exception as e:
        print(f"[DDG] Search error: {e}")
        
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
