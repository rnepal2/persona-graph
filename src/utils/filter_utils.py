import asyncio
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse # For robust hostname extraction

from src.utils.models import SearchResultItem
from src.utils.llm_utils import get_openai_response # Or your preferred LLM util

DEFAULT_BLOCKED_DOMAINS = [
    "youtube.com", "m.youtube.com", "youtu.be",
    "facebook.com", "fb.com",
    "twitter.com", "t.co",
    "instagram.com",
    "tiktok.com",
    "linkedin.com", # As per earlier rationale, can be removed if needed
    "pinterest.com",
    "reddit.com",
    "dailymotion.com",
    "vimeo.com",
]

async def filter_search_results_logic(
    results: List[SearchResultItem],
    profile_summary: str,
    agent_query_focus: str, # e.g., "Leadership style and philosophy"
    blocked_domains_list: Optional[List[str]] = None
) -> List[SearchResultItem]:
    """
    Filters a list of SearchResultItem objects based on blocked domains and LLM relevance.
    """
    if blocked_domains_list is None:
        blocked_domains_list = DEFAULT_BLOCKED_DOMAINS

    filtered_results: List[SearchResultItem] = []
    print(f"[FilterLogic] Starting with {len(results)} results. Blocked domains: {blocked_domains_list}")

    for item in results:
        # 1. Rule-based filtering (Blocked Domains)
        try:
            # item.link is already a Pydantic HttpUrl, so host is available
            domain = item.link.host
            if domain and any(blocked_domain in domain for blocked_domain in blocked_domains_list):
                print(f"[FilterLogic] Filtering out (blocked domain: {domain}): {item.link}")
                continue
        except Exception as e:
            print(f"[FilterLogic] Error parsing domain for item {item.link}: {e}. Item will be kept for LLM check.")

        # 2. LLM-based relevance filtering
        system_prompt_relevance = """
You are a meticulous relevance assessment assistant. Your task is to determine if a given web search result is relevant to a specific research goal for profiling an individual. Respond with only "YES" or "NO". Do not provide explanations or any other text.
        """
        user_prompt_relevance = f"""
Original Search Intent/Agent Focus: "{agent_query_focus}"
Overall Profile Summary of Individual: "{profile_summary}"

Search Result Details:
Title: "{item.title}"
Link: "{str(item.link)}"
Snippet: "{item.snippet or 'N/A'}"

Based on the search intent and the profile summary, is this search result relevant for further investigation? Respond with only YES or NO.
        """

        print(f"[FilterLogic] Evaluating relevance for: {item.title} (Link: {item.link})")
        llm_response = await get_openai_response(user_prompt_relevance, system_prompt=system_prompt_relevance)

        if llm_response and llm_response.strip().upper() == "YES":
            print(f"[FilterLogic] Deemed RELEVANT by LLM: {item.title}")
            filtered_results.append(item)
        else:
            if llm_response is None:
                print(f"[FilterLogic] Deemed NOT RELEVANT (LLM call failed or no response): {item.title}")
            else:
                print(f"[FilterLogic] Deemed NOT RELEVANT by LLM (Response: '{llm_response.strip()}'): {item.title}")
    
    print(f"[FilterLogic] Finished filtering. Returning {len(filtered_results)} results.")
    return filtered_results

# Example Usage for standalone testing
if __name__ == '__main__':
    async def test_filter():
        sample_results = [
            SearchResultItem(title="Relevant Article on Leadership", link="http://example.com/leadership-insights", snippet="Discusses leadership styles...", source_api="test"),
            SearchResultItem(title="Irrelevant YouTube Video", link="http://youtube.com/watch?v=123", snippet="A cat video", source_api="test"),
            SearchResultItem(title="Relevant Forbes Article", link="http://forbes.com/business-strategy", snippet="Forbes article about strategy.", source_api="test"),
            SearchResultItem(title="LinkedIn Profile Page", link="http://linkedin.com/in/johndoe", snippet="John Doe's LinkedIn.", source_api="test"),
            SearchResultItem(title="Possibly Relevant But Needs LLM Check", link="http://unknownsite.com/article", snippet="Vague snippet, could be relevant.", source_api="test"),
            SearchResultItem(title="Facebook Post", link="http://facebook.com/somepost", snippet="A post on Facebook.", source_api="test"),

        ]
        # Mock profile and focus for testing
        test_profile_summary = "Jane Doe is a CEO at ExampleCorp, focusing on AI."
        test_agent_focus = "Jane Doe's leadership style and strategic decisions."

        print(f"Original results: {len(sample_results)}")
        
        # To test LLM part, you'd need API keys. 
        # Without keys, get_openai_response returns None, so LLM will filter out items not blocked by domain.
        # To simulate LLM saying YES for "unknownsite.com" for testing without keys:
        # You could temporarily modify get_openai_response to return "YES" if prompt contains "unknownsite.com"
        # or mock the function here using unittest.mock if running this as a true unit test.
        
        filtered = await filter_search_results_logic(sample_results, test_profile_summary, test_agent_focus)
        
        print("\nFiltered results:")
        for res in filtered:
            print(f"- {res.title} (LLM relevant, source: {res.link.host})")

    asyncio.run(test_filter())
