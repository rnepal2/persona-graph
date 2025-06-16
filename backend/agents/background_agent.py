import asyncio
import nest_asyncio
from datetime import datetime
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END 
from agents.common_state import AgentState
from utils.llm_utils import get_openai_response, get_gemini_response
from utils.llm_utils import async_parse_structured_data
from utils.models import SearchResultItem
from scraping.basic_scraper import fetch_and_parse_url 
from scraping.selenium_scraper import scrape_with_selenium
from scraping.playwright_scraper import scrape_with_playwright
from utils.select_context import extract_relevant_context
from utils.filter_utils import filter_search_results_logic
from utils.filter_utils import DEFAULT_BLOCKED_DOMAINS
from pydantic import BaseModel, Field
nest_asyncio.apply()

class BackgroundAgentState(TypedDict):
    name: str
    input_profile_summary: str
    linkedin_url: Optional[str]
    generated_queries: Optional[List[str]]
    search_results: Optional[List[SearchResultItem]]
    scraped_data: Optional[List[str]]
    background_details: Optional[str]  
    metadata: Optional[List[Dict[str, Any]]]
    error_message: Optional[str]

# Placeholder Internal Nodes for BackgroundAgent Subgraph
def process_initial_input_node(state: BackgroundAgentState) -> BackgroundAgentState:
    print(">>>[BackgroundAgent] Processing initial input...")
    return state

async def generate_background_queries_node(state: BackgroundAgentState) -> BackgroundAgentState:
    print(">>>[BackgroundAgent] Generating background queries...")
    profile_summary = state.get("input_profile_summary", f"No profile summary provided for {state.get('name', 'Executive Name')}")
    system_prompt = """You are an expert biographical research assistant. Your goal is to \
    formulate targeted search queries to uncover comprehensive background information about an \
    individual, focusing on their education, early career, and foundational experiences."""

    user_prompt = f"""Generate 3-5 distinct search queries to find background information on
        {state.get("name", "Executive Name")}. This individual's current short profile summary is: \n
        "{profile_summary}". 

        The goal of the queries to collect information through web search only on:
            1. Educational background (universities, degrees, field of study, graduation years).
            2. Early career history (first few significant roles, companies, and durations).
            3. Key affiliations (e.g., board memberships, advisory roles, non-profit involvement, 
               early in their career or foundational).
            4. Notable early achievements or transitions.

        Make each query as a simple English phrase or question, suitable for a web search.
        Return the queries as a numbered list, each query on a new line.    
        """
    prompt = f"{system_prompt}, \n\n {user_prompt}"
    raw_llm_response = await get_gemini_response(prompt=prompt)

    class QueriesList(BaseModel):
        queries: List[str] = Field(
            default_factory=list,
            description="List of generated search queries for background information."
        )
    
    generated_queries = []
    if raw_llm_response:
        queries = await async_parse_structured_data(raw_llm_response, schema=QueriesList)
        generated_queries = queries.queries if queries and queries.queries else []
        print(f">>>[BackgroundAgent] LLM generated queries:")
        for i, query in enumerate(generated_queries):
            print(f"    [{i + 1}] {query}")
    else:
        print("[BackgroundAgent] LLM call failed or returned no response. Using default placeholder queries.")
        generated_queries = [f"who is {state.get('name', 'Executive Name')}?", 
                             f"professional background of {state.get('name', 'Executive Name')}",
                            ]
    state['generated_queries'] = generated_queries
    return state

async def execute_background_search_node(state: BackgroundAgentState) -> BackgroundAgentState:
    print(">>>[BackgroundAgent] Running background search with DuckDuckGo...")
    from search.duckduckgo_search import perform_duckduckgo_search
    queries = state.get('generated_queries') or []
    all_results = []
    for query in queries:
        try:
            results = await perform_duckduckgo_search(query=query, max_results=3)
            if results:
                all_results.extend(results)
        except Exception as e:
            print(f">>>[BackgroundAgent] DuckDuckGo search failed for query '{query}': {e}")
    state['search_results'] = all_results
    return state

async def scrape_background_results_node(state: BackgroundAgentState) -> BackgroundAgentState:
    agent_name = "BackgroundAgent"
    print(f">>>[{agent_name}] Scraping search results...")
    
    # CONFIGURABLE SCRAPER ORDER
    SCRAPER_ORDER = ["basic_scraper", "selenium_scraper", "playwright_scraper"]    
    current_search_results = state.get('search_results') or []
    if not current_search_results:
        print(f"[{agent_name}] No search results to scrape.")
        return state

    processed_search_results: List[SearchResultItem] = []
    MIN_CONTENT_LENGTH = 100 

    # Define scraper functions mapping
    scraper_functions = {
        "basic_scraper": lambda url: fetch_and_parse_url(str(url)),
        "selenium_scraper": lambda url: scrape_with_selenium(str(url)),
        "playwright_scraper": lambda url: scrape_with_playwright(str(url))
    }

    for item in current_search_results:
        if item.content and len(item.content) >= MIN_CONTENT_LENGTH:
            print(f"[{agent_name}] Content already exists for '{item.title}', skipping scrape...")
            processed_search_results.append(item)
            continue

        print(f"[{agent_name}] Attempting to scrape URL: {item.link}")
        scraped_text: Optional[str] = None
        scraper_used: Optional[str] = None

        # Try scrapers in the configured order
        for scraper_name in SCRAPER_ORDER:
            if scraper_used:  # If we already succeeded, break out
                break
                
            try:
                print(f"[{agent_name}] Trying {scraper_name} for {item.link}...")
                scraper_function = scraper_functions[scraper_name]
                scraped_text = await scraper_function(item.link)
                
                if scraped_text and len(scraped_text) >= MIN_CONTENT_LENGTH:
                    scraped_text = extract_relevant_context(scraped_text, search_phrase=state.get("name", "Executive Name"))
                    scraper_used = scraper_name
                    print(f"[{agent_name}] ✓ {scraper_name.upper()} succeeded for {item.link}")
                else:
                    scraped_text = None
                    print(f"[{agent_name}] ✗ {scraper_name} returned insufficient content for {item.link}")
                    
            except Exception as e:
                print(f"[{agent_name}] ✗ {scraper_name} failed for {item.link}: {e}")
                scraped_text = None
        
        if scraper_used:
            scraped_text = scraped_text.strip() if scraped_text else None
            scraped_text = ' '.join(str(scraped_text).strip().split(' ')[:2000])
            _snippet = ' '.join(str(scraped_text).strip().split(' ')[:300]) + "..." if scraped_text else None
            print(f"<<<[{agent_name}] Successfully processed {str(item.link)[:30] + '...' if len(str(item.link)) > 30 else str(item.link)} with {str(scraper_used).upper()}>>>")
            updated_item = item.model_copy(update={
                'content': scraped_text, 
                'snippet': item.snippet or (_snippet+"..." if scraped_text else None)
            })
            processed_search_results.append(updated_item)
        else:
            print(f"<<<[{agent_name}] All scrapers failed or minimal content for: {str(item.link)[:30] + '...' if len(str(item.link)) > 30 else str(item.link)}>>>")
            processed_search_results.append(item) 
        await asyncio.sleep(0)

    state['search_results'] = processed_search_results
    state['scraped_data'] = [res.content for res in processed_search_results if res.content]
    print(f"[{agent_name}] Finished scraping. Processed {len(current_search_results)} items.")
    return state

async def compile_background_details_node(state: BackgroundAgentState) -> BackgroundAgentState:
    print("[BackgroundAgent] Compiling background details...")
    
    # Collect all available data with proper null checks
    scraped_data = state.get('scraped_data') or []
    search_results = state.get('search_results') or []
    initial_input = state.get('input_profile_summary', '')
    
    # Ensure scraped_data is a list and handle None values
    if scraped_data is None:
        scraped_data = []
    elif not isinstance(scraped_data, list):
        scraped_data = [scraped_data] if scraped_data else []
    
    # Store raw data and references in metadata with proper handling
    try:
        state['metadata'] = [{
            "agent": "BackgroundAgent",
            "background_references": search_results if search_results else [],
            "raw_data": scraped_data,
            "timestamp": str(datetime.now())
        }]
    except Exception as e:
        print(f"[BackgroundAgent] Error creating metadata: {e}")
        state['metadata'] = []
    
    # Prepare context for LLM with safe iteration
    context = f"""Initial Profile Information:\n{initial_input}\n\nAdditional Information:"""
    
    try:
        # Safely iterate over scraped_data
        if scraped_data and len(scraped_data) > 0:
            for i, data in enumerate(scraped_data, 1):
                if data is not None and isinstance(data, str) and len(data.strip()) > 0:
                    context += f"\nSource {i}:\n{data[:1000]}..."
        else:
            context += "\nNo additional scraped data available."
    except Exception as e:
        print(f"[BackgroundAgent] Error processing scraped data: {e}")
        context += "\nError processing additional data."
    
    # Generate summary using LLM
    system_prompt = """You are an expert biographer and research analyst. Create a concise but comprehensive 
    background summary of the individual based on the provided information. Focus on their education, early career,
    key roles, and notable achievements. The summary should be factual and well-structured."""
    
    user_prompt = f"""Based on the following information, create a detailed background summary:
    {context}
    
    Format the summary as a clear narrative that covers:
    1. Educational background and early career foundation
    2. Professional progression and key roles
    3. Notable achievements and contributions
    4. Professional affiliations and board positions
    
    Keep the tone professional and focus on verified information."""
    prompt = f"{system_prompt}\n\n{user_prompt}"
    
    try:
        llm_response = await get_gemini_response(prompt=prompt)
        if llm_response and len(llm_response.strip()) > 0:
            summary = str(llm_response).strip()
        else:
            summary = "Unable to generate detailed background summary from available information."
    except Exception as e:
        print(f"[BackgroundAgent] Error generating summary: {e}")
        summary = f"Background analysis completed with limited information due to processing constraints."
    
    state['background_details'] = summary
    return state

async def filter_search_results_node(state: BackgroundAgentState) -> BackgroundAgentState:
    agent_name = "BackgroundAgent"
    name = state.get('name', 'Executive Name')
    print(f">>>[{agent_name}] Filtering search results...")
    current_results = state.get('search_results') or []
    if not current_results:
        print(f"[{agent_name}] No search results to filter.")
        return state

    profile_summary = state.get('input_profile_summary', '')
    agent_specific_focus_description = """Comprehensive background information including \
    education, early career history, affiliations, geographic moves, and origin stories."""

    filtered_results = await filter_search_results_logic(
        name=name,
        results=current_results,
        profile_summary=profile_summary,
        agent_query_focus=agent_specific_focus_description,
        blocked_domains_list=DEFAULT_BLOCKED_DOMAINS
    )
    print(f"[{agent_name}] Original results: {len(current_results)}, Filtered results: {len(filtered_results)}")
    state['search_results'] = filtered_results
    return state

# Agent subgraph
background_graph = StateGraph(BackgroundAgentState)

background_graph.add_node("process_initial_input", process_initial_input_node)
background_graph.add_node("generate_background_queries", generate_background_queries_node)
background_graph.add_node("execute_search", execute_background_search_node)
background_graph.add_node("scrape_results", scrape_background_results_node)
background_graph.add_node("filter_search_results", filter_search_results_node)
background_graph.add_node("compile_details", compile_background_details_node)

background_graph.set_entry_point("process_initial_input")
background_graph.add_edge("process_initial_input", "generate_background_queries")
background_graph.add_edge("generate_background_queries", "execute_search")
background_graph.add_edge("execute_search", "scrape_results") 
background_graph.add_edge("scrape_results", "filter_search_results")
background_graph.add_edge("filter_search_results", "compile_details")
background_graph.add_edge("compile_details", END)
background_subgraph_app = background_graph.compile()

async def background_agent_node(state: AgentState) -> AgentState: 
    print("\n>>>[BackgroundAgent] Starting background search agent...")
    print("Name: ", state.get("name", "Executive Name"))

    try:
        parent_input = state.get("leader_initial_input")
        if parent_input is None:
            print("[BackgroundAgentWrapper] Warning: No leader_initial_input found in parent state.")
            parent_input = "No specific profile input provided for background analysis."

        initial_subgraph_state = BackgroundAgentState(
            name=state.get("name", "Executive Name"),
            input_profile_summary=parent_input,
            linkedin_url=None,
            generated_queries=None,
            search_results=None,
            scraped_data=None,
            background_details=None,
            metadata=None,
            error_message=None
        )

        try:
            print(f"[BackgroundAgentWrapper] Invoking subgraph with initial state")
            subgraph_final_state = await background_subgraph_app.ainvoke(initial_subgraph_state)
            print(f"[BackgroundAgentWrapper] Subgraph finished successfully.")
        except Exception as e:
            error_msg = f"BackgroundAgent subgraph failed: {str(e)}"
            print(f"[BackgroundAgentWrapper] Error: {error_msg}")
            
            # Set error but don't set next_agent - let graph handle routing
            state['error_message'] = error_msg
            state['background_info'] = f"Background information could not be generated due to: {str(e)}"
            return state

        if not subgraph_final_state:
            error_msg = "BackgroundAgent: Subgraph returned no state."
            state['error_message'] = error_msg
            state['background_info'] = "Background information could not be generated."
            print(f"[BackgroundAgentWrapper] Error: {error_msg}")
            return state

        # Extract results with fallbacks
        background_summary = subgraph_final_state.get('background_details')
        if isinstance(background_summary, str) and background_summary.strip():
            state['background_info'] = background_summary
        else:
            print("[BackgroundAgentWrapper] Warning: No valid background summary generated.")
            state['background_info'] = "Background information could not be generated from available sources."

        # Add metadata if available
        if subgraph_final_state.get('metadata'):
            state['metadata'] = state.get('metadata', []) + subgraph_final_state['metadata']
        print("[BackgroundAgentWrapper] Background agent completed successfully.")
        
    except Exception as e:
        error_msg = f"BackgroundAgent critical error: {str(e)}"
        print(f"[BackgroundAgentWrapper] Critical Error: {error_msg}")
        state['error_message'] = error_msg
        state['background_info'] = "Background analysis encountered a critical error."
        
    return state
