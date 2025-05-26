# src/search_utils.py

from duckduckgo_search import DDGS
from typing import List, Dict

# Conceptual: Import API key from config.
# Although DDGS().text might not require it, other features or engines might.
from src.config import DUCKDUCKGO_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY # Ensure config loading

def perform_duckduckgo_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Performs a web search using DuckDuckGo and returns a list of results.

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
    # ddgs = DDGS(headers={'x-api-key': DUCKDUCKGO_API_KEY}) # Example if key was needed for DDGS object

    try:
        print(f"Performing DuckDuckGo search for: '{query}' with max_results={max_results}")
        # DDGS().text() is a generator. We need to iterate and collect results.
        ddgs_results = DDGS().text(keywords=query, max_results=max_results)
        
        if ddgs_results:
            for result in ddgs_results:
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
            print("No results returned from DDGS().text")
            
    except Exception as e:
        print(f"Error during DuckDuckGo search: {e}")
        # results will remain an empty list
    
    return results

if __name__ == "__main__":
    print("Testing search_utils.py...")

    # This demonstrates that API keys can be loaded from config.py
    print(f"Attempting to load API keys from src.config:")
    print(f"  OPENAI_API_KEY loaded: {'Yes' if OPENAI_API_KEY else 'No (or empty)'}")
    print(f"  GEMINI_API_KEY loaded: {'Yes' if GEMINI_API_KEY else 'No (or empty)'}")
    print(f"  DUCKDUCKGO_API_KEY loaded: {'Yes' if DUCKDUCKGO_API_KEY else 'No (or empty)'}")
    
    sample_query = "LangGraph use cases"
    print(f"\nPerforming search for query: '{sample_query}'")
    
    search_results = perform_duckduckgo_search(sample_query, max_results=3)
    
    if search_results:
        print(f"\nFound {len(search_results)} results:")
        for i, res in enumerate(search_results, 1):
            print(f"\nResult {i}:")
            print(f"  Title: {res['title']}")
            print(f"  URL: {res['href']}")
            print(f"  Snippet: {res['body']}")
    else:
        print("No search results found or an error occurred.")

    print("\nsearch_utils.py test finished.")
