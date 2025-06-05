from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any

class SearchResultItem(BaseModel):
    title: str
    link: HttpUrl
    snippet: Optional[str] = None
    source_api: str  # e.g., "duckduckgo", "serpapi", "tavily"
    content: Optional[str] = None  # For Tavily or pre-scraped content
    raw_result: Optional[Dict[str, Any]] = None # To store the original API output

# Example usage (can be commented out or within an if __name__ == "__main__": block for testing)
if __name__ == '__main__':
    example_result = SearchResultItem(
        title="Example Search Result",
        link="http://example.com",
        snippet="This is an example snippet.",
        source_api="duckduckgo",
        raw_result={"original_field": "original_value"}
    )
    print(example_result.model_dump_json(indent=2))

    example_tavily = SearchResultItem(
        title="Tavily Example",
        link="http://example.com/tavily",
        snippet="Snippet from Tavily.",
        source_api="tavily",
        content="This is the pre-scraped content from Tavily."
    )
    print(example_tavily.model_dump_json(indent=2))
