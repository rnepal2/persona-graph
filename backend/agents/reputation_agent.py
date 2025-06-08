# src/agents/reputation_agent.py
import os
import asyncio
import nest_asyncio
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from agents.common_state import AgentState
from pydantic import BaseModel, Field
from utils.llm_utils import get_gemini_response, async_parse_structured_data
from utils.models import SearchResultItem
from utils.search_utils import perform_duckduckgo_search
from scraping.basic_scraper import fetch_and_parse_url
from scraping.selenium_scraper import scrape_with_selenium
from scraping.playwright_scraper import scrape_with_playwright
from utils.filter_utils import filter_search_results_logic, DEFAULT_BLOCKED_DOMAINS

# Apply nest_asyncio to handle nested event loops
nest_asyncio.apply()

# Define the internal state for the Reputation Agent subgraph
class ReputationAgentState(TypedDict):
    name: str
    input_profile_summary: str
    generated_queries: Optional[List[str]]
    search_results: Optional[List[SearchResultItem]] # Updated type hint
    scraped_data: Optional[List[str]]
    reputation_report: Optional[str]
    error_message: Optional[str]
    metadata: Optional[List[Dict[str, Any]]] # New field

# Placeholder Internal Nodes for ReputationAgent Subgraph
async def generate_reputation_queries_node(state: ReputationAgentState) -> ReputationAgentState:
    print("[ReputationAgent] Generating reputation queries via LLM...")

    profile_summary = state.get("input_profile_summary", "No profile summary provided.")
    profile_name_placeholder = state.get("name", "Executive Name")

    system_prompt = """You are a specialist in public reputation and media analysis. Your goal is 
    to devise search queries that gather information on an executive's public image, media presence, 
    and notable recognitions or controversies."""

    user_prompt = f"""Generate 3-5 distinct search queries to assess the public reputation of 
    {profile_name_placeholder}. Their current profile summary is: "{profile_summary}". Focus the queries on:
    1. News articles, press releases, or official announcements mentioning them.
    2. Awards, honors, or significant recognitions they have received.
    3. Any public controversies, legal issues, or criticisms involving them or their companies during their tenure.
    4. Their reputation within their specific industry or among peers.

    Return the queries as a numbered list, each query on a new line."""
    
    prompt = f"{system_prompt}\n\n{user_prompt}"
    raw_llm_response = await get_gemini_response(prompt=prompt)

    class QueriesList(BaseModel):
        queries: List[str] = Field(description="List of generated queries for reputation research.")

    if raw_llm_response:
        try:
            parsed_data = await async_parse_structured_data(raw_llm_response, schema=QueriesList)
            print(f"[ReputationAgent] LLM generated queries: {parsed_data.queries}")
            generated_queries = parsed_data.queries
        except Exception as e:
            print(f"[ReputationAgent] Error parsing queries: {e}")
            # Fallback to simple text parsing if structured parsing fails
            lines = raw_llm_response.strip().split('\n')
            generated_queries = [line.strip().split('. ', 1)[-1] for line in lines if line.strip()]
    else:
        print("[ReputationAgent] LLM call failed or returned no response. Using default placeholder queries.")
        generated_queries = [
            f"{profile_name_placeholder} awards honors recognition achievements",
            f"{profile_name_placeholder} public reputation media coverage",
            f"{profile_name_placeholder} industry leadership influence"
        ]

    state['generated_queries'] = generated_queries
    return state

async def execute_reputation_search_node(state: ReputationAgentState) -> ReputationAgentState:
    print("[ReputationAgent] Running search with DuckDuckGo...")
    from utils.search_utils import perform_duckduckgo_search
    
    queries = state.get('generated_queries') or []
    all_results = []
    
    for query in queries:
        try:
            results = await perform_duckduckgo_search(query=query, max_results=3)
            if results:
                all_results.extend(results)
        except Exception as e:
            print(f"[ReputationAgent] DuckDuckGo search failed for query '{query}': {e}")
            
    state['search_results'] = all_results
    return state

async def scrape_reputation_results_node(state: ReputationAgentState) -> ReputationAgentState:
    agent_name = "ReputationAgent"
    print(f"[{agent_name}] Scraping reputation results...")
    current_search_results = state.get('search_results') or []
    if not current_search_results:
        print(f"[{agent_name}] No search results to scrape.")
        return state

    processed_search_results: List[SearchResultItem] = []
    MIN_CONTENT_LENGTH = 100

    for item in current_search_results:
        if getattr(item, 'content', None) and len(item.content) >= MIN_CONTENT_LENGTH:
            print(f"[{agent_name}] Content already exists for '{item.title}', skipping scrape.")
            processed_search_results.append(item)
            continue

        print(f"[{agent_name}] Attempting to scrape URL: {item.link}")
        scraped_text: Optional[str] = None
        scraper_used: Optional[str] = None

        # 1. Try Basic Scraper
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

        # 3. Try Selenium Scraper if Playwright failed
        if not scraper_used:
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
    state['scraped_data'] = [res.content for res in processed_search_results if getattr(res, 'content', None)]
    print(f"[{agent_name}] Finished scraping. Processed {len(current_search_results)} items.")
    return state

# Node to filter search results for reputation relevance (if not already present)
async def filter_search_results_node(state: ReputationAgentState) -> ReputationAgentState:
    agent_name = "ReputationAgent"
    print(f"[{agent_name}] Filtering search results...")
    current_results = state.get('search_results') or []
    if not current_results:
        print(f"[{agent_name}] No search results to filter.")
        return state

    profile_summary = state.get('input_profile_summary', '')
    agent_specific_focus_description = "Public sentiment, media perception, awards, controversies, and overall reputation of the executive."

    filtered_results = await filter_search_results_logic(
        results=current_results,
        profile_summary=profile_summary,
        agent_query_focus=agent_specific_focus_description,
        blocked_domains_list=DEFAULT_BLOCKED_DOMAINS
    )
    print(f"[{agent_name}] Original results: {len(current_results)}, Filtered results: {len(filtered_results)}")
    state['search_results'] = filtered_results
    return state

# Refactored compile_reputation_report_node to use LLM and filtered search results
async def compile_reputation_report_node(state: ReputationAgentState) -> ReputationAgentState:
    print("[ReputationAgent] Compiling reputation report using LLM and filtered search results...")
    search_results = state.get('search_results') or []
    profile_summary = state.get('input_profile_summary', '')

    # Build context from filtered search results (title + content)
    context_chunks = []
    for item in search_results:
        title = getattr(item, 'title', None) or ''
        content = getattr(item, 'content', None) or ''
        if title or content:
            context_chunks.append(f"Title: {title}\nContent: {content}\n")
    context_str = "\n---\n".join(context_chunks)
    if not context_str:
        context_str = "No relevant search results found."

    prompt = f"""You are an expert executive reputation analyst. Using the 
    following search results, write a concise, evidence-based summary 
    of the individual's public reputation, media perception, awards, 
    controversies, and overall reputation. Only use information present 
    in the search results. Do not speculate or invent details.\n\n
    Profile summary: {profile_summary}\n\n
    Search Results:\n{context_str}\n\n
    Reputation Profile Summary (2-4 paragraphs):"""
    try:
        llm_response = await get_gemini_response(prompt)
        report = llm_response.strip() if llm_response else "No reputation information could be generated from the available data."
    except Exception as e:
        print(f"[ReputationAgent] Error during LLM call: {e}")
        report = f"Error generating reputation report: {e}"

    state['reputation_report'] = report
    # Add metadata item
    if state.get('metadata') is None:
        state['metadata'] = []
    state['metadata'].append({"source": "ReputationAgent", "info": "Reputation report generated"})
    print("[ReputationAgent] Reputation report generated and added to metadata.")
    return state

# set up subgraph for ReputationAgent
reputation_graph = StateGraph(ReputationAgentState)

reputation_graph.add_node("generate_reputation_queries", generate_reputation_queries_node)
reputation_graph.add_node("execute_search", execute_reputation_search_node)
reputation_graph.add_node("filter_search_results", filter_search_results_node)
reputation_graph.add_node("scrape_results", scrape_reputation_results_node)
reputation_graph.add_node("compile_report", compile_reputation_report_node)

reputation_graph.set_entry_point("generate_reputation_queries")
reputation_graph.add_edge("generate_reputation_queries", "execute_search")
reputation_graph.add_edge("execute_search", "filter_search_results")
reputation_graph.add_edge("filter_search_results", "scrape_results")
reputation_graph.add_edge("scrape_results", "compile_report")
reputation_graph.add_edge("compile_report", END)

reputation_subgraph_app = reputation_graph.compile()

# Wrapper node for the ReputationAgent subgraph
async def reputation_agent_node(state: AgentState) -> AgentState: # Changed to async def
    """Main entry point for ReputationAgent that interfaces with the broader pipeline"""
    print("\n[ReputationAgent] Starting reputation analysis...")
    
    try:
        enriched_summary = state.get('leader_initial_input', '')
        background_info = state.get('background_info', '')
        
        if background_info and isinstance(background_info, str):
            enriched_summary += f"\n\nBackground Information:\n{background_info}"
        
        # Initialize state with proper error handling
        try:
            reputation_state = ReputationAgentState(
                name=state.get("name", "Executive Name"),
                input_profile_summary=enriched_summary,
                generated_queries=None,
                search_results=None,
                scraped_data=None,
                reputation_report=None,
                error_message=None,
                metadata=None
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize ReputationAgentState: {str(e)}")
        
        # Run the reputation subgraph with proper async handling
        try:
            final_reputation_state = await reputation_subgraph_app.ainvoke(reputation_state)
            if not final_reputation_state:
                raise ValueError("Reputation subgraph returned None state")
            
            # Update the common state with reputation info
            state['reputation_info'] = final_reputation_state.get('reputation_report')
            if final_reputation_state.get('metadata'):
                state['metadata'] = state.get('metadata', []) + final_reputation_state['metadata']
            
            # Set next agent only if successful
            state['next_agent_to_call'] = "StrategyAgent"
            
        except Exception as e:
            raise RuntimeError(f"Reputation subgraph execution failed: {str(e)}")
            
    except Exception as e:
        error_msg = f"Reputation agent failed: {str(e)}"
        print(f"[ReputationAgent] Error: {error_msg}")
        state['error_message'] = error_msg
        # Don't set next_agent_to_call on error to allow error handling in main graph
        
    print("[ReputationAgent] Finished processing.")
    return state
