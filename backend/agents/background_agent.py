# src/agents/background_agent.py
import os
import asyncio
from typing import TypedDict, List, Optional, Dict, Any

TEST_MODE = True

from langgraph.graph import StateGraph, END
from agents.common_state import AgentState
from utils.llm_utils import get_openai_response, get_gemini_response
from utils.models import SearchResultItem
from scraping.basic_scraper import fetch_and_parse_url
from scraping.selenium_scraper import scrape_with_selenium
from scraping.playwright_scraper import scrape_with_playwright
from utils.filter_utils import filter_search_results_logic, DEFAULT_BLOCKED_DOMAINS

from utils.llm_utils import async_parse_structured_data
from pydantic import BaseModel, Field
from utils.config import GEMINI_API_KEY
from langchain_google_genai import ChatGoogleGenerativeAI


class BackgroundAgentState(TypedDict):
    input_profile_summary: str
    linkedin_url: Optional[str]
    generated_queries: Optional[List[str]]
    search_results: Optional[List[SearchResultItem]]
    scraped_data: Optional[List[str]]
    background_details: Optional[Dict[str, Any]]
    metadata: Optional[List[Dict[str, Any]]]
    error_message: Optional[str]

# Placeholder Internal Nodes for BackgroundAgent Subgraph
def process_initial_input_node(state: BackgroundAgentState) -> BackgroundAgentState:
    print("[BackgroundAgent] Processing initial input...")
    # Placeholder: Extract LinkedIn URL if present, prepare for query generation
    # For now, just sets a placeholder detail.
    if state.get('background_details') is None:
        state['background_details'] = {}
    state['background_details']['initial_processing'] = "Processed initial input."
    # Potentially extract state.get('input_profile_summary') to find a linkedin_url
    # state['linkedin_url'] = "http://linkedin.com/in/placeholder" # Example
    return state

async def extract_profile_name_from_summary(profile_summary: str) -> Optional[str]:
    """
    Uses the Gemini LLM structured data parser to extract the person's name from the profile summary.
    Returns the extracted name or None if not found.
    """
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not set. Cannot extract profile name.")
        return None
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    class NameSchema(BaseModel):
        name: Optional[str] = Field(default=None, description="The full name of the person if available in the profile summary.")

    try:
        result = await async_parse_structured_data(profile_summary, schema=NameSchema, llm=llm)
        if result and getattr(result, "name", None):
            return result.name
    except Exception as e:
        print(f"[extract_profile_name_from_summary] Error: {e}")
    return None

async def generate_background_queries_node(state: BackgroundAgentState) -> BackgroundAgentState:
    print("[BackgroundAgent] Generating background queries via LLM...")

    profile_summary = state.get("input_profile_summary", "No profile summary provided.")
    # Extract the profile name using the structured data parser
    profile_name = await extract_profile_name_from_summary(profile_summary)
    profile_name_placeholder = profile_name or "the individual"
    print("Individual Name: ", profile_name_placeholder)

    system_level_prompt = """You are an expert biographical research assistant. Your goal is to \
    formulate targeted search queries to uncover comprehensive background information about an \
    individual, focusing on their education, early career, and foundational experiences."""

    user_facing_prompt = f"""Generate 3-5 distinct search queries to find background information on
        {profile_name_placeholder}. This individual's current profile summary is: \n"{profile_summary}". 
        Focus the queries on:
            1. Educational background (universities, degrees, field of study, graduation years).
            2. Early career history (first few significant roles, companies, and durations).
            3. Key affiliations (e.g., board memberships, advisory roles, non-profit involvement, 
               early in their career or foundational).
            4. Notable early achievements or transitions.

            Return the queries as a numbered list, each query on a new line.
            Example:
            1. {profile_name_placeholder} education history
            2. {profile_name_placeholder} career history

            Make each query as a simple English phrase or question, suitable for a web search engine.
        """
    # raw_llm_response = await get_openai_response(user_facing_prompt, system_prompt=system_level_prompt)
    raw_llm_response = await get_gemini_response(prompt=f"{system_level_prompt}, \n\n {user_facing_prompt}")

    class QueriesList(BaseModel):
        queries: List[str] = Field(
            default_factory=list,
            description="List of generated search queries for background information."
        )
    
    generated_queries = []
    if raw_llm_response:
        queries = await async_parse_structured_data(raw_llm_response, schema=QueriesList)
        generated_queries = queries.queries if queries and queries.queries else []
        print(f"[BackgroundAgent] LLM generated queries: {generated_queries}")
    else:
        print("[BackgroundAgent] LLM call failed or returned no response. Using default placeholder queries.")
        generated_queries = ["default background query 1", "default background query 2"] # Fallback
    state['generated_queries'] = generated_queries
    return state

def execute_background_search_node_placeholder(state: BackgroundAgentState) -> BackgroundAgentState:
    print("[BackgroundAgent] Executing background search (placeholder)...")
    dummy_results = [
        SearchResultItem(title="John Doe Education History - University XYZ", link="http://example.edu/johndoe-alumni", snippet="John Doe graduated with a BS in Computer Science.", source_api="placeholder_bg"),
        SearchResultItem(title="John Doe's Early Career at OldCorp", link="http://newsarchive.com/johndoe-oldcorp-role", snippet="Details about John Doe's first major role.", source_api="placeholder_bg"),
        SearchResultItem(title="Funny Cat Videos by John Doe", link="http://youtube.com/watch?v=johndoecats", snippet="John Doe's personal cat video channel.", source_api="placeholder_bg"),
        SearchResultItem(title="Latest advancements in unrelated Quantum Physics", link="http://physicsworld.com/quantum-breakthrough", snippet="A new discovery in quantum entanglement.", source_api="placeholder_bg"),
        SearchResultItem(title="John Doe - LinkedIn Profile", link="http://linkedin.com/in/johndoe-profile", snippet="Professional profile of John Doe.", source_api="placeholder_bg")
    ]
    state['search_results'] = dummy_results
    return state

async def execute_background_search_node(state: BackgroundAgentState) -> BackgroundAgentState:
    print("[BackgroundAgent] Executing background search using DuckDuckGo API...")
    from utils.search_utils import perform_duckduckgo_search
    queries = state.get('generated_queries') or []
    all_results = []
    for query in queries:
        try:
            results = await perform_duckduckgo_search(query=query, max_results=3)
            if results:
                all_results.extend(results)
        except Exception as e:
            print(f"[BackgroundAgent] DuckDuckGo search failed for query '{query}': {e}")
    state['search_results'] = all_results
    return state

# Updated TEST_MODE logic
async def scrape_background_results_node(state: BackgroundAgentState) -> BackgroundAgentState:
    agent_name = "BackgroundAgent"
    print(f"[{agent_name}] Scraping search results (TEST_MODE: {TEST_MODE})...")
    current_search_results = state.get('search_results') or []
    if not current_search_results:
        print(f"[{agent_name}] No search results to scrape.")
        return state

    processed_search_results: List[SearchResultItem] = []
    MIN_CONTENT_LENGTH = 100 

    for item in current_search_results:
        if item.content and len(item.content) >= MIN_CONTENT_LENGTH:
            print(f"[{agent_name}] Content already exists for '{item.title}', skipping scrape...")
            processed_search_results.append(item)
            continue

        print(f"[{agent_name}] Attempting to scrape URL: {item.link}")
        scraped_text: Optional[str] = None
        scraper_used: Optional[str] = None

        # 1. Try Basic Scraper (Always try this one)
        try:
            print(f"[{agent_name}] Trying basic_scraper for {item.link}...")
            scraped_text = await fetch_and_parse_url(str(item.link))
            if scraped_text and len(scraped_text) >= MIN_CONTENT_LENGTH:
                scraper_used = "basic_scraper"
            else:
                scraped_text = None 
        except Exception as e:
            print(f"[{agent_name}] Basic_scraper failed for {item.link}: {e}")
            scraped_text = None

        # 2. Try Playwright Scraper if basic failed
        if not scraper_used:
            if TEST_MODE:
                print(f"[{agent_name}] TEST_MODE: Simulating Playwright call for {item.link}.")
                # Option A: Simulate successful scrape with dummy content
                scraped_text = f"Simulated Playwright content for {item.link}"
                if len(scraped_text) >= MIN_CONTENT_LENGTH: # Check length for consistency
                   scraper_used = "playwright_scraper (simulated)"
                else:
                   scraped_text = None
            else:
                try:
                    print(f"[{agent_name}] Trying playwright_scraper for {item.link}...")
                    scraped_text = await scrape_with_playwright(str(item.link))
                    if scraped_text and len(scraped_text) >= MIN_CONTENT_LENGTH:
                        scraper_used = "playwright_scraper"
                    else:
                        scraped_text = None
                except Exception as e:
                    print(f"[{agent_name}] Playwright_scraper failed for {item.link}: {e}")
                    scraped_text = None
        
        # 3. Try Selenium Scraper if previous attempts failed
        if not scraper_used:
            if TEST_MODE:
                print(f"[{agent_name}] TEST_MODE: Simulating Selenium call for {item.link}.")
                scraped_text = f"Simulated Selenium content for {item.link}"
                if len(scraped_text) >= MIN_CONTENT_LENGTH:
                   scraper_used = "selenium_scraper (simulated)"
                else:
                   scraped_text = None
            else:
                try:
                    print(f"[{agent_name}] Trying selenium_scraper for {item.link}...")
                    scraped_text = await scrape_with_selenium(str(item.link))
                    if scraped_text and len(scraped_text) >= MIN_CONTENT_LENGTH:
                        scraper_used = "selenium_scraper"
                    else:
                        scraped_text = None
                except Exception as e:
                    print(f"[{agent_name}] Selenium_scraper failed for {item.link}: {e}")
                    scraped_text = None
        
        if scraper_used:
            print(f"[{agent_name}] Successfully processed {item.link} using {scraper_used}.")
            updated_item = item.model_copy(update={
                'content': scraped_text, 
                'snippet': item.snippet or (scraped_text[:250]+"..." if scraped_text else None)
            })
            processed_search_results.append(updated_item)
        else:
            print(f"[{agent_name}] All scrapers failed or returned insufficient content for {item.link}.")
            processed_search_results.append(item) 
        await asyncio.sleep(0)

    state['search_results'] = processed_search_results
    state['scraped_data'] = [res.content for res in processed_search_results if res.content]
    print(f"[{agent_name}] Finished scraping. Processed {len(current_search_results)} items.")
    return state

def compile_background_details_node(state: BackgroundAgentState) -> BackgroundAgentState:
    print("[BackgroundAgent] Compiling background details...")
    if state.get('background_details') is None:
        state['background_details'] = {}
    state['background_details']['education'] = "Placeholder University"
    state['background_details']['early_career'] = "Placeholder First Job"
    if state.get('metadata') is None:
        state['metadata'] = []
    state['metadata'].append({"source": "BackgroundAgent", "info": "Compiled background details"})
    return state

async def filter_search_results_node(state: BackgroundAgentState) -> BackgroundAgentState:
    agent_name = "BackgroundAgent"
    print(f"[{agent_name}] Filtering search results...")
    current_results = state.get('search_results') or []
    if not current_results:
        print(f"[{agent_name}] No search results to filter.")
        return state

    profile_summary = state.get('input_profile_summary', '')
    agent_specific_focus_description = "Comprehensive background information including education, early career history, affiliations, geographic moves, and origin stories."

    filtered_results = await filter_search_results_logic(
        results=current_results,
        profile_summary=profile_summary,
        agent_query_focus=agent_specific_focus_description,
        blocked_domains_list=DEFAULT_BLOCKED_DOMAINS # Using the default list
    )
    print(f"[{agent_name}] Original results: {len(current_results)}, Filtered results: {len(filtered_results)}")
    state['search_results'] = filtered_results
    return state

# Agent subgraph
background_graph = StateGraph(BackgroundAgentState)

background_graph.add_node("process_initial_input", process_initial_input_node)
background_graph.add_node("generate_background_queries", generate_background_queries_node)
background_graph.add_node("execute_search", execute_background_search_node)
background_graph.add_node("filter_search_results", filter_search_results_node) # Added node
background_graph.add_node("scrape_results", scrape_background_results_node)
background_graph.add_node("compile_details", compile_background_details_node)

background_graph.set_entry_point("process_initial_input")
background_graph.add_edge("process_initial_input", "generate_background_queries")
background_graph.add_edge("generate_background_queries", "execute_search")
background_graph.add_edge("execute_search", "filter_search_results") # Changed edge
background_graph.add_edge("filter_search_results", "scrape_results") # Added edge
background_graph.add_edge("scrape_results", "compile_details")
background_graph.add_edge("compile_details", END)
background_subgraph_app = background_graph.compile()

async def background_agent_node(state: AgentState) -> AgentState: # Changed to async def
    print("\n>>> Entering [BackgroundAgent]...")

    # 1. Transform parent state to initial subgraph state
    parent_input = state.get("leader_initial_input")
    if parent_input is None:
        print("[BackgroundAgentWrapper] Warning: No leader_initial_input found in parent state.")
        parent_input = "No specific profile input provided for background analysis."

    initial_subgraph_state = BackgroundAgentState(
        input_profile_summary=parent_input,
        linkedin_url=None,
        generated_queries=None,
        search_results=None,
        scraped_data=None,
        background_details=None,
        metadata=list(state.get('metadata') or []), 
        error_message=None
    )

    # 2. Invoke the subgraph
    try:
        print(f"[BackgroundAgentWrapper] Invoking subgraph with initial state: {{'input_profile_summary': '{parent_input[:50]}...'}}")
        subgraph_final_state = await background_subgraph_app.ainvoke(initial_subgraph_state)
        print(f"[BackgroundAgentWrapper] Subgraph finished. Final state: {subgraph_final_state}")
    except Exception as e:
        print(f"[BackgroundAgentWrapper] Error invoking subgraph: {e}")
        state['error_message'] = ((state.get('error_message') or '') + f" BackgroundAgent failed: {e}").strip()
        subgraph_final_state = None

    # 3. Transform subgraph result back to parent state
    if subgraph_final_state:
        details = subgraph_final_state.get("background_details")
        subgraph_error = subgraph_final_state.get("error_message")
        subgraph_generated_metadata = subgraph_final_state.get("metadata")

        if subgraph_error:
            state['error_message'] = ((state.get('error_message') or '') + f" BackgroundSubgraphError: {subgraph_error}").strip()
            print(f"[BackgroundAgentWrapper] Subgraph reported an error: {subgraph_error}")

        if details:
            # 'background_info' will be added to AgentState in the next plan step
            state['background_info'] = details
        else:
            print("[BackgroundAgentWrapper] No background_details found in subgraph final state.")
            # Do not overwrite a more specific error from the subgraph itself
            if not subgraph_error:
                 state['error_message'] = ((state.get('error_message') or '') + " BackgroundAgent: No background details generated.").strip()
        
        if subgraph_generated_metadata:
            state['metadata'] = subgraph_generated_metadata

    else: # Handles case where subgraph_final_state itself is None due to exception
        if not state.get('error_message'): # Don't overwrite specific exception message
             state['error_message'] = ((state.get('error_message') or '') + " BackgroundAgent: Subgraph invocation failed critically.").strip()
        # In this case, state['metadata'] would still hold the original list passed as a copy

    # 4. Set next agent in parent graph
    print("[BackgroundAgentWrapper] Setting next agent to LeadershipAgent.")
    state['next_agent_to_call'] = "LeadershipAgent"
    return state
