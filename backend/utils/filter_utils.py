import asyncio
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse 
from utils.models import SearchResultItem
from utils.llm_utils import get_openai_response, get_gemini_response

DEFAULT_BLOCKED_DOMAINS = [
    "facebook.com", "fb.com",
    "twitter.com", "t.co",
    "instagram.com",
    "tiktok.com",
    "pinterest.com",
    "reddit.com",
    "dailymotion.com",
    "vimeo.com",
]

async def filter_search_results_logic(
    results: List[SearchResultItem],
    profile_summary: str,
    agent_query_focus: str,
    blocked_domains_list: Optional[List[str]] = None
) -> List[SearchResultItem]:
    """
    Filters a list of SearchResultItem objects based on blocked domains and LLM relevance.
    First filters by blocked domains, then performs parallel LLM relevance checks.
    """
    if blocked_domains_list is None:
        blocked_domains_list = DEFAULT_BLOCKED_DOMAINS

    # Step 1: Filter by blocked domains first
    domain_filtered_results: List[SearchResultItem] = []
    print(f"\n>>>[FilterSearchResult] Starting with {len(results)} results. Blocked domains: {blocked_domains_list}")

    for item in results:
        try:
            domain = item.link.host
            if domain and any(blocked_domain in domain for blocked_domain in blocked_domains_list):
                print(f">>>[FilterLogic] Filtering out (blocked domain: {domain}): {item.link}")
                continue
            domain_filtered_results.append(item)
        except Exception as e:
            print(f">>>[FilterLogic] Error parsing domain for item {item.link}: {e}. Item will be kept for LLM check.")
            domain_filtered_results.append(item)
    print(f">>>[FilterLogic] {len(domain_filtered_results)} items passed domain filtering")

    # Step 2: Prepare LLM tasks for parallel execution
    async def check_relevance(item: SearchResultItem) -> tuple[SearchResultItem, bool]:
        system_prompt = """You are a meticulous relevance assessment assistant. Your task is to
        determine if a given web search result is relevant to a specific individual of interest."""
        
        user_prompt = f"""
            Original Search Intent/Agent Focus: "{agent_query_focus}"
            Overall Profile Summary of Individual: "{profile_summary}"

            Search Result Details:
            Title: "{item.title}"
            Link: "{str(item.link)}"
            Snippet: "{item.snippet or 'N/A'}"

            Reminder: This search result should be assessed for this specific individual based on the profile not 
            just the name, as there might be many people with the same name.

            Based on the search intent and the profile summary, is this search result relevant for 
            further investigation? Respond with only YES or NO.
        """
        print(f"[RankSearchItem] Evaluating relevance for: {item.title} (Link: {item.link})")
        prompt = f"{system_prompt} \n\n {user_prompt}"
        llm_response = await get_gemini_response(prompt=prompt)
        
        is_relevant = False
        if llm_response and llm_response.strip().upper() == "YES":
            print(f"[RankSearchItem] RELEVANT by LLM: {item.title}")
            is_relevant = True
        else:
            if llm_response is None:
                print(f">>>[RankSearchItem] NOT RELEVANT (LLM call failed or no response), Title: {item.title}")
            else:
                print(f">>>[RankSearchItem] NOT RELEVANT, Title: {item.title}")
        
        return item, is_relevant

    # Step 3: Execute LLM relevance checks in parallel
    relevance_tasks = [check_relevance(item) for item in domain_filtered_results]
    relevance_results = await asyncio.gather(*relevance_tasks)

    # Step 4: Filter based on LLM relevance results
    filtered_results = [item for item, is_relevant in relevance_results if is_relevant]
    
    print(f"<<<[RankSearchItem] Finished filtering. Returning {len(filtered_results)} results>>>\n")
    return filtered_results

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
        # Mock profile
        test_profile_summary = "Jane Doe is a CEO at ExampleCorp, focusing on AI."
        test_agent_focus = "Jane Doe's leadership style and strategic decisions."

        print(f"Original results: {len(sample_results)}")
        filtered = await filter_search_results_logic(sample_results, test_profile_summary, test_agent_focus)
        
        print("\nFiltered results:")
        for res in filtered:
            print(f"- {res.title} (LLM relevant, source: {res.link.host})")

    asyncio.run(test_filter())
