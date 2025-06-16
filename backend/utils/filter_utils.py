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
    name: str,
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
        system_prompt = """You are a meticulous researcher and fact-checker specializing in identity disambiguation."""
        
        user_prompt = """
            [TASK]
            Your task is to determine with high confidence if the provided article is about our specific 
            'Person of Interest' or simply someone else with the same name. You must avoid false positives.

            [PERSON OF INTEREST DETAILS]
            - Name: "{name}"
            - Profile: "{profile_summary}"
            - Context of Search: "{agent_query_focus}"

            [ARTICLE DETAILS]
            - Title: {item.title}
            - Snippet: {item.snippet}
            - Link: {item.link}

            [INSTRUCTIONS]
            Follow this step-by-step process:
            1.  **Analyze Profile:** Read the 'Person of Interest Details' to understand their key identifiers (e.g., company, role, location, field of expertise).
            2.  **Analyze Article:** Extract key identifying details from the 'ARTICLE DETAILS'.
            3.  **Compare and Contrast:**
                - Look for details that match with the profile.
                - Any details that CONFLICT or are INCONSISTENT, eg. same name but different educational and professional background than provided profile summary.
                - If the article is too generic to make a confident decision, return irrelevant.
                - Use provided profile summary and agent query focus to to check conflict/alignment.
                - For example, same person is less likely to be a Data Scientist at a company and Professor at a different University as the same time.
            4.  **Decision Criteria:** Make objective decision based on the analysis about article relevance.

            [DECISION & OUTPUT FORMAT]
            Relevance: "YES" or "NO"
        """
        prompt = f"{system_prompt} \n\n {user_prompt}"
        llm_response = await get_gemini_response(prompt=prompt, model_name="gemini-2.0-flash")
        
        is_relevant = False
        if llm_response and 'YES' in llm_response.strip().upper():
            is_relevant = True
        return item, is_relevant

    # Step 3: Execute LLM relevance checks in parallel
    relevance_tasks = [check_relevance(item) for item in domain_filtered_results]
    relevance_results = await asyncio.gather(*relevance_tasks)

    print(f">>>[RankSearchItem] Completed LLM relevance checks on {len(relevance_results)} articles:")
    for item, is_relevant in relevance_results:
        if is_relevant:
            print(f"\n>>>[RankSearchItem] ✓ RELEVANT: {item.title} (Link: {item.link})")
            print(f">>>[Article Snippet]: {item.snippet}")
        else:
            print(f"\n>>>[RankSearchItem] ✗ NOT RELEVANT: {item.title} (Link: {item.link})")
            print(f">>>[Article Snippet]: {item.snippet}")

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
