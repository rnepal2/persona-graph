# src/agents/leadership_agent.py
import os
import asyncio
import nest_asyncio
from typing import TypedDict, List, Optional, Dict, Any 
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from agents.common_state import AgentState 
from utils.llm_utils import get_openai_response, get_gemini_response
from utils.llm_utils import async_parse_structured_data
from utils.models import SearchResultItem 
from scraping.basic_scraper import fetch_and_parse_url 
from scraping.selenium_scraper import scrape_with_selenium 
from scraping.playwright_scraper import scrape_with_playwright
from utils.filter_utils import filter_search_results_logic
from utils.filter_utils import DEFAULT_BLOCKED_DOMAINS
nest_asyncio.apply()

class LeadershipAgentState(TypedDict):
    name: str
    input_profile_summary: str
    generated_queries: Optional[List[str]]
    search_results: Optional[List[SearchResultItem]] 
    scraped_data: Optional[List[str]]
    leadership_report: Optional[str]
    error_message: Optional[str]
    metadata: Optional[List[Dict[str, Any]]] 

# Placeholder Internal Nodes for LeadershipAgent Subgraph
async def generate_leadership_queries_node(state: LeadershipAgentState) -> LeadershipAgentState:
    print("[LeadershipAgent] Generating leadership queries via LLM...")
    profile_summary = state.get("input_profile_summary", "")
    profile_name_placeholder = state.get("name", "Executive Name")
    
    system_prompt = """You are an expert leadership analyst. Your goal is to formulate targeted 
    search queries to uncover comprehensive information about an individual's leadership style, 
    decision-making approach, and team management capabilities."""

    user_prompt = f"""Generate 3-7 distinct search queries to find information about the 
    leadership qualities and style of {profile_name_placeholder}. Their current profile 
    summary is: "{profile_summary}". Focus on queries that would find:
    1. Descriptions of their leadership style or management philosophy (e.g., articles, interviews).
    2. Examples of significant decisions they made and the reported outcomes.
    3. Information about their team building, mentorship, or communication style.
    4. Quotes from them or about them regarding their leadership.

    Importantly, if the executive holds or held a DRI role for a business or product in a large company,
    include queries (one or more depending upon their leadership history) that will gather information 
    on how the corresponding product or business performed during their tenure. Any insight that informs 
    measurable outcomes of their leadership is highly valuabe.

    Return the queries as a numbered list, each query on a new line."""
    
    prompt = f"{system_prompt}\n\n{user_prompt}"
    raw_llm_response = await get_gemini_response(prompt=prompt)

    class QueriesList(BaseModel):
        queries: List[str] = Field(
            default_factory=list,
            description="List of generated search queries for leadership information."
        )

    if raw_llm_response:
        # Properly await the async parse function
        try:
            parsed_data = await async_parse_structured_data(raw_llm_response, QueriesList)
            print(f"[LeadershipAgent] LLM generated queries: {parsed_data.queries}")
            generated_queries = parsed_data.queries
        except Exception as e:
            print(f"[LeadershipAgent] Error parsing queries: {e}")
            # Fallback to simple text parsing if structured parsing fails
            lines = raw_llm_response.strip().split('\n')
            generated_queries = [line.strip().split('. ', 1)[-1] for line in lines if line.strip()]
    else:
        print("[LeadershipAgent] Warning: No response from LLM, using fallback queries")
        generated_queries = [
            f"{profile_name_placeholder} leadership style management philosophy",
            f"{profile_name_placeholder} team building mentorship",
            f"{profile_name_placeholder} business decisions outcomes"
        ]

    state['generated_queries'] = generated_queries
    return state

async def execute_search_node(state: LeadershipAgentState) -> LeadershipAgentState:
    print("[LeadershipAgent] Running search with DuckDuckGo...")
    from search.duckduckgo_search import perform_duckduckgo_search
    
    queries = state.get('generated_queries') or []
    all_results = []
    
    for query in queries:
        try:
            results = await perform_duckduckgo_search(query=query, max_results=3)
            if results:
                all_results.extend(results)
        except Exception as e:
            print(f"[LeadershipAgent] DuckDuckGo search failed for query '{query}': {e}")
            
    state['search_results'] = all_results
    return state

async def scrape_results_node(state: LeadershipAgentState) -> LeadershipAgentState:
    agent_name = "LeadershipAgent"
    print(f"[{agent_name}] Scraping search results...")
    
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
            print(f"[{agent_name}] Content already exists for '{item.title}', skipping scrape.")
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
                    scraper_used = scraper_name
                    print(f"[{agent_name}] ✓ {scraper_name.upper()} succeeded for {item.link}")
                else:
                    scraped_text = None
                    print(f"[{agent_name}] ✗ {scraper_name} returned insufficient content for {item.link}")
                    
            except Exception as e:
                print(f"[{agent_name}] ✗ {scraper_name} failed for {item.link}: {e}")
                scraped_text = None

        if scraper_used:
            print(f"[{agent_name}] Successfully scraped {item.link} using {scraper_used}.")
            updated_item = item.model_copy(update={
                'content': scraped_text, 
                'snippet': item.snippet or (scraped_text[:250]+"..." if scraped_text else None)
            })
            processed_search_results.append(updated_item)
        else:
            print(f"[{agent_name}] All scrapers failed for {item.link}.")
            processed_search_results.append(item) # Add original item

        await asyncio.sleep(0) # Yield control

    # Update the main state with processed results
    state['search_results'] = processed_search_results
    state['scraped_data'] = [res.content for res in processed_search_results if res.content]
    print(f"[{agent_name}] Finished scraping. Processed {len(current_search_results)} items.")
    return state

async def filter_search_results_node(state: LeadershipAgentState) -> LeadershipAgentState:
    agent_name = "LeadershipAgent"
    name = state.get('name', 'Executive Name')
    print(f"[{agent_name}] Filtering search results...")
    current_results = state.get('search_results') or []
    if not current_results:
        print(f"[{agent_name}] No search results to filter.")
        return state

    profile_summary = state.get('input_profile_summary', '')
    agent_specific_focus_description = (
        "Leadership style, management philosophy, decision-making, team building, mentorship, communication style, and leadership outcomes."
    )

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

async def compile_report_node(state: LeadershipAgentState) -> LeadershipAgentState:
    print("[LeadershipAgent] Compiling leadership report using LLM and filtered search results...")
    search_results = state.get('search_results') or []
    profile_summary = state.get('input_profile_summary', '')

    context_chunks = []
    for item in search_results:
        title = getattr(item, 'title', None) or ''
        content = getattr(item, 'content', None) or ''
        if title or content:
            context_chunks.append(f"Title: {title}\nContent: {content}\n")
    context_str = "\n---\n".join(context_chunks)
    if not context_str:
        context_str = "No relevant search results found."

    prompt = f"""You are an expert executive profile analyst. Using the following search 
    results, write a concise, evidence-based summary of the individual's leadership style, 
    decision-making, and team interactions. Only use information present in the search 
    results. Do not speculate or invent details.\n\n
    Profile summary: 
    {profile_summary}\n\n
    Search Results:\n{context_str}\n\n

    If the executive holds or held DRI roles for a business or product in a large company,
    make sure to include measurable outcome of their leadership based on the performance of
    the business or product they led if related information is gathered through the search and 
    is present in the context provided to you above.

    Leadership Profile Summary (2-4 paragraphs, depending upon available information):"""
    try:
        llm_response = await get_gemini_response(prompt=prompt)
        report = llm_response.strip() if llm_response else "No leadership information could be generated from the available data."
    except Exception as e:
        print(f"[LeadershipAgent] Error during LLM call: {e}")
        report = f"Error generating leadership report: {e}"

    state['leadership_report'] = report
    if state.get('metadata') is None:
        state['metadata'] = []
    state['metadata'].append({"source": "LeadershipAgent", "info": "Leadership report generated"})
    print("[LeadershipAgent] Leadership report generated and added to metadata.")
    return state

# LeadershipAgent Subgraph
leadership_graph = StateGraph(LeadershipAgentState)

leadership_graph.add_node("generate_leadership_queries", generate_leadership_queries_node)
leadership_graph.add_node("execute_search", execute_search_node)
leadership_graph.add_node("filter_search_results", filter_search_results_node)
leadership_graph.add_node("scrape_results", scrape_results_node)
leadership_graph.add_node("compile_report", compile_report_node)

leadership_graph.set_entry_point("generate_leadership_queries")
leadership_graph.add_edge("generate_leadership_queries", "execute_search")
leadership_graph.add_edge("execute_search", "scrape_results")
leadership_graph.add_edge("scrape_results", "filter_search_results")
leadership_graph.add_edge("filter_search_results", "compile_report")
leadership_graph.add_edge("compile_report", END)

leadership_subgraph_app = leadership_graph.compile()

async def leadership_agent_node(state: AgentState) -> AgentState:
    """Main entry point for LeadershipAgent that interfaces with the broader pipeline"""
    print("\n>>>[LeadershipAgent] Starting leadership agent...")
    
    try:
        # Create enriched profile from background info
        enriched_summary = state.get('leader_initial_input', '')
        background_info = state.get('background_info', '')
        
        if background_info and isinstance(background_info, str):
            enriched_summary += f"\n\nBackground Information:\n{background_info}"
        
        # Initialize state with proper error handling
        try:
            leadership_state = LeadershipAgentState(
                name=state.get("name", "Executive Name"),
                input_profile_summary=enriched_summary,
                generated_queries=None,
                search_results=None,
                scraped_data=None,
                leadership_report=None,
                error_message=None,
                metadata=None
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize LeadershipAgentState: {str(e)}")
        
        # Run the leadership subgraph with proper async handling
        try:
            # Use ainvoke() instead of direct call
            final_leadership_state = await leadership_subgraph_app.ainvoke(leadership_state)
            if not final_leadership_state:
                raise ValueError("Leadership subgraph returned None state")
            
            # Update the common state with leadership info
            state['leadership_info'] = final_leadership_state.get('leadership_report')
            if final_leadership_state.get('metadata'):
                state['metadata'] = state.get('metadata', []) + final_leadership_state['metadata']
            
            # Set next agent only if successful
            state['next_agent_to_call'] = "ReputationAgent"
            
        except Exception as e:
            raise RuntimeError(f"Leadership subgraph execution failed: {str(e)}")
            
    except Exception as e:
        error_msg = f"Leadership agent failed: {str(e)}"
        print(f"[LeadershipAgent] Error: {error_msg}")
        state['error_message'] = error_msg
        # Don't set next_agent_to_call on error to allow error handling in main graph
        
    print(">>>[LeadershipAgent] Finished processing.")
    return state
