# src/agents/background_agent.py
from typing import TypedDict, List, Optional, Dict, Any
import asyncio

TEST_MODE = True # Defined at the top of the file

from langgraph.graph import StateGraph, END
from .common_state import AgentState
from utils.llm_utils import get_openai_response
from utils.models import SearchResultItem
from scraping.basic_scraper import fetch_and_parse_url
from scraping.selenium_scraper import scrape_with_selenium
from scraping.playwright_scraper import scrape_with_playwright
# from src.scraping.llm_scraper import scrape_with_llm # Deferred for now
from utils.filter_utils import filter_search_results_logic, DEFAULT_BLOCKED_DOMAINS


class BackgroundAgentState(TypedDict):
    input_profile_summary: str # Likely from parent, could include LinkedIn URL or other initial pointers
    linkedin_url: Optional[str]
    generated_queries: Optional[List[str]]
    search_results: Optional[List[SearchResultItem]] # Updated type hint
    scraped_data: Optional[List[str]]
    # For structured background info like education, early career, affiliations
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

async def generate_background_queries_node(state: BackgroundAgentState) -> BackgroundAgentState:
    print("[BackgroundAgent] Generating background queries via LLM...")

    profile_summary = state.get("input_profile_summary", "No profile summary provided.")
    # For now, let's assume profile_name can be derived or is part of the summary.
    # A more robust solution would be to have a dedicated 'profile_name' field.
    # We'll use a placeholder if it's hard to extract.
    profile_name_placeholder = "the individual" # Or try to extract from summary

    # Constructing prompts as per the subtask description (OpenAI expects system_prompt as a kwarg)
    # The main user-facing instruction goes into the first 'prompt' argument.
    # The role-setting or system-level instruction goes into 'system_prompt'.
    
    # The problem description has this structure:
    # user_prompt = f"""... {profile_name_placeholder} ... {profile_summary} ..."""
    # raw_llm_response = await get_openai_response(user_prompt, system_prompt=system_prompt)
    # This means the first arg to get_openai_response is the detailed user_prompt, and system_prompt is the kwarg.

    system_level_prompt = """
You are an expert biographical research assistant. Your goal is to formulate targeted search queries to uncover comprehensive background information about an individual, focusing on their education, early career, and foundational experiences.
            """
    # This is the main prompt for the LLM's task
    user_facing_prompt = f"""
Generate 3-5 distinct search queries to find background information on {profile_name_placeholder}. This individual's current profile summary is: "{profile_summary}". Focus the queries on:
1. Educational background (universities, degrees, field of study, graduation years).
2. Early career history (first few significant roles, companies, and durations).
3. Key affiliations (e.g., board memberships, advisory roles, non-profit involvement, early in their career or foundational).
4. Notable early achievements or transitions.

Return the queries as a numbered list, each query on a new line.
Example:
1. {profile_name_placeholder} education history
2. {profile_name_placeholder} early career
            """
    
    # The `get_openai_response` function is defined as:
    # async def get_openai_response(prompt: str, system_prompt: Optional[str] = None, model_name: str = "gpt-3.5-turbo")
    # So, user_facing_prompt is the `prompt` (first arg), and system_level_prompt is the `system_prompt` (kwarg).
    raw_llm_response = await get_openai_response(user_facing_prompt, system_prompt=system_level_prompt)

    generated_queries = []
    if raw_llm_response:
        queries = raw_llm_response.strip().split('\n')
        for q in queries:
            # Remove potential numbering (e.g., "1. ", "1) ")
            cleaned_q = q.split('.', 1)[-1].split(')', 1)[-1].strip()
            if cleaned_q: # Avoid empty strings
                generated_queries.append(cleaned_q)
        print(f"[BackgroundAgent] LLM generated queries: {generated_queries}")
    else:
        print("[BackgroundAgent] LLM call failed or returned no response. Using default placeholder queries.")
        generated_queries = ["default background query 1", "default background query 2"] # Fallback

    state['generated_queries'] = generated_queries
    return state

def execute_background_search_node(state: BackgroundAgentState) -> BackgroundAgentState:
    print("[BackgroundAgent] Executing background search (placeholder)...")
    # Dummy results to test filtering for background agent
    dummy_results = [
        SearchResultItem(title="John Doe Education History - University XYZ", link="http://example.edu/johndoe-alumni", snippet="John Doe graduated with a BS in Computer Science.", source_api="placeholder_bg"),
        SearchResultItem(title="John Doe's Early Career at OldCorp", link="http://newsarchive.com/johndoe-oldcorp-role", snippet="Details about John Doe's first major role.", source_api="placeholder_bg"),
        SearchResultItem(title="Funny Cat Videos by John Doe", link="http://youtube.com/watch?v=johndoecats", snippet="John Doe's personal cat video channel.", source_api="placeholder_bg"),
        SearchResultItem(title="Latest advancements in unrelated Quantum Physics", link="http://physicsworld.com/quantum-breakthrough", snippet="A new discovery in quantum entanglement.", source_api="placeholder_bg"),
        SearchResultItem(title="John Doe - LinkedIn Profile", link="http://linkedin.com/in/johndoe-profile", snippet="Professional profile of John Doe.", source_api="placeholder_bg")
    ]
    state['search_results'] = dummy_results
    # print(f"[BackgroundAgent] Populated search_results with {len(dummy_results)} dummy items.")
    return state

# Updated scrape_background_results_node with TEST_MODE logic from the prompt
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
            print(f"[{agent_name}] Content already exists for '{item.title}', skipping scrape.")
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
                # To test different scenarios, you can vary what dummy data is returned:
                # Option A: Simulate successful scrape with dummy content
                scraped_text = f"Simulated Playwright content for {item.link}"
                if len(scraped_text) >= MIN_CONTENT_LENGTH: # Check length for consistency
                   scraper_used = "playwright_scraper (simulated)"
                else: # Should not happen with fixed dummy string but good practice
                   scraped_text = None
                # Option B: Simulate Playwright failing to get enough content or erroring
                # scraped_text = None 
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
                # Option A: Simulate successful scrape
                scraped_text = f"Simulated Selenium content for {item.link}"
                if len(scraped_text) >= MIN_CONTENT_LENGTH:
                   scraper_used = "selenium_scraper (simulated)"
                else:
                   scraped_text = None
                # Option B: Simulate failure
                # scraped_text = None
            else: # Actual call for non-TEST_MODE
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
    # Update 'scraped_data' for compatibility if it's still used elsewhere,
    # though ideally the system should transition to using 'search_results[i].content'.
    state['scraped_data'] = [res.content for res in processed_search_results if res.content]
    
    print(f"[{agent_name}] Finished scraping. Processed {len(current_search_results)} items.")
    return state

def compile_background_details_node(state: BackgroundAgentState) -> BackgroundAgentState:
    print("[BackgroundAgent] Compiling background details...")
    if state.get('background_details') is None:
        state['background_details'] = {}
    state['background_details']['education'] = "Placeholder University"
    state['background_details']['early_career'] = "Placeholder First Job"
    # Also append to metadata as an example
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
    # Define a specific focus for this agent to guide the LLM in relevance assessment
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

# Instantiate and Build the Subgraph
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

# AgentState should be imported from .common_state
# BackgroundAgentState and background_subgraph_app are defined above in this file.

async def background_agent_node(state: AgentState) -> AgentState: # Changed to async def
    print("[MainGraph] Calling BackgroundAgent subgraph...")

    # 1. Transform parent state to initial subgraph state
    parent_input = state.get("leader_initial_input")
    if parent_input is None:
        print("[BackgroundAgentWrapper] Warning: No leader_initial_input found in parent state.")
        parent_input = "No specific profile input provided for background analysis."

    initial_subgraph_state = BackgroundAgentState(
        input_profile_summary=parent_input,
        linkedin_url=None, # Subgraph can populate this if found in input_profile_summary
        generated_queries=None,
        search_results=None,
        scraped_data=None,
        background_details=None, # Subgraph will populate this
        metadata=list(state.get('metadata') or []), # Pass a shallow copy
        error_message=None
    )

    # 2. Invoke the subgraph
    try:
        print(f"[BackgroundAgentWrapper] Invoking subgraph with initial state: {{'input_profile_summary': '{parent_input[:50]}...'}}")
        subgraph_final_state = await background_subgraph_app.ainvoke(initial_subgraph_state) # Changed to await and ainvoke
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
            state['metadata'] = subgraph_generated_metadata # Assign the list from subgraph (which includes original + new)
            # print(f"[BackgroundAgentWrapper] Updated parent metadata to: {state['metadata']}")
        # If subgraph_generated_metadata is None (e.g. subgraph error before metadata init), parent metadata remains unchanged (from initial pass-through)

    else: # Handles case where subgraph_final_state itself is None due to exception
        if not state.get('error_message'): # Don't overwrite specific exception message
             state['error_message'] = ((state.get('error_message') or '') + " BackgroundAgent: Subgraph invocation failed critically.").strip()
        # In this case, state['metadata'] would still hold the original list passed as a copy

    # 4. Set next agent in parent graph
    print("[BackgroundAgentWrapper] Setting next agent to LeadershipAgent.")
    state['next_agent_to_call'] = "LeadershipAgent"

    return state
