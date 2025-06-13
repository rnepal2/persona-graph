# src/agents/strategy_agent.py
import os
import asyncio
import nest_asyncio
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from agents.common_state import AgentState
from pydantic import BaseModel, Field
from utils.llm_utils import get_gemini_response, get_openai_response
from utils.llm_utils import async_parse_structured_data
from utils.models import SearchResultItem
from scraping.basic_scraper import fetch_and_parse_url
from scraping.selenium_scraper import scrape_with_selenium
from scraping.playwright_scraper import scrape_with_playwright
from utils.filter_utils import filter_search_results_logic
from utils.filter_utils import DEFAULT_BLOCKED_DOMAINS
nest_asyncio.apply()

class StrategyAgentState(TypedDict):
    name: str
    input_profile_summary: str
    generated_queries: Optional[List[str]]
    search_results: Optional[List[SearchResultItem]] # Updated type hint
    scraped_data: Optional[List[str]]
    strategy_report: Optional[str]
    error_message: Optional[str]
    metadata: Optional[List[Dict[str, Any]]] # New field

async def generate_strategy_queries_node(state: StrategyAgentState) -> StrategyAgentState:
    print("[StrategyAgent] Generating strategy queries via LLM...")

    profile_summary = state.get("input_profile_summary", "No profile summary provided.")
    profile_name_placeholder = state.get("name", "Executive Name")

    system_prompt = """You are a business strategy and financial analyst. Your task is to formulate 
    search queries that will uncover an executive's strategic initiatives, business impact, and 
    involvement in major organizational changes or achievements."""

    user_prompt = f"""Generate 3-5 distinct search queries to identify the strategic contributions 
    and business impact of {profile_name_placeholder}. Their current profile summary is: 
    "{profile_summary}". Focus the queries on finding information related to:
    1. Specific business units, products, or markets they were responsible for and their performance.
    2. Major strategic initiatives they led (e.g., M&A, digital transformation, market expansion, turnarounds).
    3. Quantifiable business results or KPIs achieved under their leadership (e.g., revenue growth, market share 
    changes, innovation milestones).
    4. Their role in company vision, long-term strategy, or significant investments.

    Return the queries as a numbered list, each query on a new line.
    """
    prompt = f"{system_prompt}\n\n{user_prompt}"
    raw_llm_response = await get_gemini_response(prompt=prompt)

    class QueriesList(BaseModel):
        queries: List[str] = Field(description="List of generated queries for strategy research.")

    if raw_llm_response:
        try:
            parsed_data = await async_parse_structured_data(raw_llm_response, schema=QueriesList)
            print(f"[StrategyAgent] LLM generated queries: {parsed_data.queries}")
            generated_queries = parsed_data.queries
        except Exception as e:
            print(f"[StrategyAgent] Error parsing queries: {e}")
            # Fallback to simple text parsing if structured parsing fails
            lines = raw_llm_response.strip().split('\n')
            generated_queries = [line.strip().split('. ', 1)[-1] for line in lines if line.strip()]
    else:
        print("[StrategyAgent] LLM call failed or returned no response. Using default placeholder queries.")
        generated_queries = [
            f"{profile_name_placeholder} strategic initiatives business impact",
            f"{profile_name_placeholder} business transformation achievements",
            f"{profile_name_placeholder} company performance leadership"
        ]

    state['generated_queries'] = generated_queries
    return state

async def execute_strategy_search_node(state: StrategyAgentState) -> StrategyAgentState:
    print("[StrategyAgent] Running search with DuckDuckGo...")
    from search.duckduckgo_search import perform_duckduckgo_search
    
    queries = state.get('generated_queries') or []
    all_results = []
    
    for query in queries:
        try:
            results = await perform_duckduckgo_search(query=query, max_results=3)
            if results:
                all_results.extend(results)
        except Exception as e:
            print(f"[StrategyAgent] DuckDuckGo search failed for query '{query}': {e}")
            
    state['search_results'] = all_results
    return state

async def scrape_strategy_results_node(state: StrategyAgentState) -> StrategyAgentState:
    agent_name = "StrategyAgent"
    print(f"[{agent_name}] Scraping strategy results...")

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
        if getattr(item, 'content', None) and len(item.content) >= MIN_CONTENT_LENGTH:
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

async def compile_strategy_report_node(state: StrategyAgentState) -> StrategyAgentState:
    print("[StrategyAgent] Compiling strategy report using LLM and filtered search results...")
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

    prompt = f"""You are an expert executive strategy analyst. Using the following search results, 
    write a concise, evidence-based summary of the individual's strategic contributions,
    M&A activity, product leadership, strategic initaitves, and boardroom influence. Only use 
    information present in the search results relevant for the related executive. 
    Do not speculate or invent any details.\n\n
    Profile summary: {profile_summary}\n\n
    Search Results:\n{context_str}\n\n
    Strategy Profile Summary (2-4 paragraphs, depending upon the provided context information):
    """
    try:
        llm_response = await get_gemini_response(prompt)
        report = llm_response.strip() if llm_response else "No strategy information could be generated from the available data."
    except Exception as e:
        print(f"[StrategyAgent] Error during LLM call: {e}")
        report = f"Error generating strategy report: {e}"

    state['strategy_report'] = report
    # Add metadata item
    if state.get('metadata') is None:
        state['metadata'] = []
    state['metadata'].append({"source": "StrategyAgent", "info": "Strategy report generated"})
    print("[StrategyAgent] Strategy report generated and added to metadata.")
    return state

async def filter_search_results_node(state: StrategyAgentState) -> StrategyAgentState:
    agent_name = "StrategyAgent"
    name = state.get('name', 'Executive Name')
    print(f"[{agent_name}] Filtering search results...")
    current_results = state.get('search_results') or []
    if not current_results:
        print(f"[{agent_name}] No search results to filter.")
        return state

    profile_summary = state.get('input_profile_summary', '')
    agent_specific_focus_description = "Strategic contributions, business impact, M&A activity, product leadership, measurable business results, and boardroom influence."

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

# Update subgraph: remove analyze_data node and its edge, use async compile_strategy_report_node
strategy_graph = StateGraph(StrategyAgentState)

strategy_graph.add_node("generate_strategy_queries", generate_strategy_queries_node)
strategy_graph.add_node("execute_search", execute_strategy_search_node)
strategy_graph.add_node("filter_search_results", filter_search_results_node)
strategy_graph.add_node("scrape_results", scrape_strategy_results_node)
strategy_graph.add_node("compile_report", compile_strategy_report_node)

strategy_graph.set_entry_point("generate_strategy_queries")
strategy_graph.add_edge("generate_strategy_queries", "execute_search")
strategy_graph.add_edge("execute_search", "scrape_results")
strategy_graph.add_edge("scrape_results", "filter_search_results")
strategy_graph.add_edge("filter_search_results", "compile_report")
strategy_graph.add_edge("compile_report", END)

strategy_subgraph_app = strategy_graph.compile()

async def strategy_agent_node(state: AgentState): # Changed to async def
    """Main entry point for StrategyAgent that interfaces with the broader pipeline"""
    print("\n>>>[StrategyAgent] Starting strategy analysis...")
    
    try:
        enriched_summary = state.get('leader_initial_input', '')
        background_info = state.get('background_info', '')
        
        if background_info and isinstance(background_info, str):
            enriched_summary += f"\n\nBackground Information:\n{background_info}"
        
        # Initialize state with proper error handling
        try:
            strategy_state = StrategyAgentState(
                name=state.get("name", "Executive Name"),
                input_profile_summary=enriched_summary,
                generated_queries=None,
                search_results=None,
                scraped_data=None,
                strategy_report=None,
                error_message=None,
                metadata=None
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize StrategyAgentState: {str(e)}")
        
        # Run the strategy subgraph with proper async handling
        try:
            final_strategy_state = await strategy_subgraph_app.ainvoke(strategy_state)
            if not final_strategy_state:
                raise ValueError("Strategy subgraph returned None state")
            
            # Update the common state with strategy info
            state['strategy_info'] = final_strategy_state.get('strategy_report')
            if final_strategy_state.get('metadata'):
                state['metadata'] = state.get('metadata', []) + final_strategy_state['metadata']
            
            # Set next agent only if successful
            state['next_agent_to_call'] = "ProfileAggregatorAgent"
            
        except Exception as e:
            raise RuntimeError(f"Strategy subgraph execution failed: {str(e)}")
            
    except Exception as e:
        error_msg = f"Strategy agent failed: {str(e)}"
        print(f"[StrategyAgent] Error: {error_msg}")
        state['error_message'] = error_msg
        
    print("[StrategyAgent] Finished processing.")
    return state
    print("[StrategyAgent] Finished processing.")
    return state
