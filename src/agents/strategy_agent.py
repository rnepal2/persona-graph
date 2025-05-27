# src/agents/strategy_agent.py
from typing import TypedDict, List, Optional, Dict, Any # Ensure Any is imported
from langgraph.graph import StateGraph, END
from .common_state import AgentState # For the wrapper node later
from src.utils.llm_utils import get_openai_response # Added import
from src.utils.models import SearchResultItem # Added import

# Define the internal state for the Strategy Agent subgraph
from src.utils.filter_utils import filter_search_results_logic, DEFAULT_BLOCKED_DOMAINS # Added import

class StrategyAgentState(TypedDict):
    input_profile_summary: str
    generated_queries: Optional[List[str]]
    search_results: Optional[List[SearchResultItem]] # Updated type hint
    scraped_data: Optional[List[str]]
    strategy_report: Optional[str]
    error_message: Optional[str]
    metadata: Optional[List[Dict[str, Any]]] # New field

# Placeholder Internal Nodes for StrategyAgent Subgraph
async def generate_strategy_queries_node(state: StrategyAgentState) -> StrategyAgentState:
    print("[StrategyAgent] Generating strategy queries via LLM...")

    profile_summary = state.get("input_profile_summary", "No profile summary provided.")
    profile_name_placeholder = "the individual" # Or derive from summary

    system_prompt = """
You are a business strategy and financial analyst. Your task is to formulate search queries that will uncover an executive's strategic initiatives, business impact, and involvement in major organizational changes or achievements.
            """
    user_prompt = f"""
Generate 3-5 distinct search queries to identify the strategic contributions and business impact of {profile_name_placeholder}. Their current profile summary is: "{profile_summary}". Focus the queries on finding information related to:
1. Specific business units, products, or markets they were responsible for and their performance.
2. Major strategic initiatives they led (e.g., M&A, digital transformation, market expansion, turnarounds).
3. Quantifiable business results or KPIs achieved under their leadership (e.g., revenue growth, market share changes, innovation milestones).
4. Their role in company vision, long-term strategy, or significant investments.

Return the queries as a numbered list, each query on a new line.
            """

    raw_llm_response = await get_openai_response(user_prompt, system_prompt=system_prompt)

    generated_queries = []
    if raw_llm_response:
        queries = raw_llm_response.strip().split('\n')
        for q in queries:
            cleaned_q = q.split('.', 1)[-1].split(')', 1)[-1].strip()
            if cleaned_q:
                generated_queries.append(cleaned_q)
        print(f"[StrategyAgent] LLM generated queries: {generated_queries}")
    else:
        print("[StrategyAgent] LLM call failed or returned no response. Using default placeholder queries.")
        generated_queries = ["default strategy query 1", "default strategy query 2"]

    state['generated_queries'] = generated_queries
    return state

def execute_strategy_search_node(state: StrategyAgentState) -> StrategyAgentState:
    print("[StrategyAgent] Executing search for strategy (placeholder)...")
    # Dummy results for StrategyAgent
    dummy_results = [
        SearchResultItem(title="Jane Doe's Impact on Innovate Inc. Market Share", link="http://financialnews.com/innovate-market-share-doe", snippet="Analysis of market share growth under Jane Doe's strategic initiatives.", source_api="placeholder_strat"),
        SearchResultItem(title="Innovate Inc. M&A Strategy Led by Jane Doe", link="http://mergerweekly.com/innovate-inc-ma-doe", snippet="Details of recent M&A activities directed by Jane Doe.", source_api="placeholder_strat"),
        SearchResultItem(title="Jane Doe's Reddit AMA on Company Vision", link="http://reddit.com/r/IAmA/comments/janedoe_ama", snippet="Jane Doe answers questions about company vision on Reddit.", source_api="placeholder_strat"), # Blocked domain
        SearchResultItem(title="Gardening Tips for Urban Dwellers", link="http://urbangarden.com/tips", snippet="How to grow vegetables in small city spaces.", source_api="placeholder_strat"), # Irrelevant
        SearchResultItem(title="Jane Doe's Keynote on Future of Tech", link="http://techconference.com/jane-doe-keynote-summary", snippet="Summary of Jane Doe's keynote speech on future technology trends and company direction.", source_api="placeholder_strat")
    ]
    state['search_results'] = dummy_results
    return state

def scrape_strategy_results_node(state: StrategyAgentState) -> StrategyAgentState:
    print("[StrategyAgent] Scraping strategy results...")
    state['scraped_data'] = ["scraped strategy content from strat_url1"]
    return state

def analyze_strategy_data_node(state: StrategyAgentState) -> StrategyAgentState:
    print("[StrategyAgent] Analyzing strategy data...")
    state['strategy_report'] = "Preliminary analysis: Leader's strategy appears innovative." # Placeholder
    return state

def compile_strategy_report_node(state: StrategyAgentState) -> StrategyAgentState:
    print("[StrategyAgent] Compiling final strategy report...")
    state['strategy_report'] = (state.get('strategy_report', "") + " Final strategy report compiled.").strip()
    return state

async def filter_search_results_node(state: StrategyAgentState) -> StrategyAgentState:
    agent_name = "StrategyAgent"
    print(f"[{agent_name}] Filtering search results...")
    current_results = state.get('search_results') or []
    if not current_results:
        print(f"[{agent_name}] No search results to filter.")
        return state

    profile_summary = state.get('input_profile_summary', '')
    agent_specific_focus_description = "Strategic contributions, business impact, M&A activity, product leadership, measurable business results, and boardroom influence."

    filtered_results = await filter_search_results_logic(
        results=current_results,
        profile_summary=profile_summary,
        agent_query_focus=agent_specific_focus_description,
        blocked_domains_list=DEFAULT_BLOCKED_DOMAINS
    )
    print(f"[{agent_name}] Original results: {len(current_results)}, Filtered results: {len(filtered_results)}")
    state['search_results'] = filtered_results
    return state

# Instantiate and Build the Subgraph
strategy_graph = StateGraph(StrategyAgentState)

strategy_graph.add_node("generate_strategy_queries", generate_strategy_queries_node)
strategy_graph.add_node("execute_search", execute_strategy_search_node)
strategy_graph.add_node("filter_search_results", filter_search_results_node) # Added node
strategy_graph.add_node("scrape_results", scrape_strategy_results_node)
strategy_graph.add_node("analyze_data", analyze_strategy_data_node)
strategy_graph.add_node("compile_report", compile_strategy_report_node)

strategy_graph.set_entry_point("generate_strategy_queries")
strategy_graph.add_edge("generate_strategy_queries", "execute_search")
strategy_graph.add_edge("execute_search", "filter_search_results") # Changed edge
strategy_graph.add_edge("filter_search_results", "scrape_results") # Added edge
strategy_graph.add_edge("scrape_results", "analyze_data")
strategy_graph.add_edge("analyze_data", "compile_report")
strategy_graph.add_edge("compile_report", END)

strategy_subgraph_app = strategy_graph.compile()

# Wrapper node for the StrategyAgent subgraph
async def strategy_agent_node(state: AgentState) -> AgentState: # Changed to async def
    print("[MainGraph] Calling StrategyAgent subgraph...")

    # 1. Transform parent state to initial subgraph state
    parent_input = state.get("leader_initial_input")
    if parent_input is None:
        print("[StrategyAgentWrapper] Warning: No leader_initial_input found in parent state.")
        parent_input = "No specific profile input provided for strategy analysis." # Default

    initial_subgraph_state = StrategyAgentState(
        input_profile_summary=parent_input,
        generated_queries=None,
        search_results=None,
        scraped_data=None,
        strategy_report=None,
        error_message=None,
        metadata=list(state.get('metadata') or []) # Pass a shallow copy
    )

    # 2. Invoke the subgraph
    try:
        print(f"[StrategyAgentWrapper] Invoking subgraph with initial state: {{'input_profile_summary': '{parent_input[:50]}...'}}")
        subgraph_final_state = await strategy_subgraph_app.ainvoke(initial_subgraph_state) # Changed to await and ainvoke
        print(f"[StrategyAgentWrapper] Subgraph finished. Final state: {subgraph_final_state}")
    except Exception as e:
        print(f"[StrategyAgentWrapper] Error invoking subgraph: {e}")
        state['error_message'] = ((state.get('error_message') or '') + f" StrategyAgent failed: {e}").strip()
        subgraph_final_state = None

    # 3. Transform subgraph result back to parent state
    if subgraph_final_state:
        report = subgraph_final_state.get("strategy_report")
        subgraph_error = subgraph_final_state.get("error_message")

        if subgraph_error:
            state['error_message'] = ((state.get('error_message') or '') + f" StrategySubgraphError: {subgraph_error}").strip()
            print(f"[StrategyAgentWrapper] Subgraph reported an error: {subgraph_error}")

        if report:
            if state.get('strategy_info') is None:
                state['strategy_info'] = []
            state['strategy_info'].append(report)
        else:
            print("[StrategyAgentWrapper] No report found in subgraph final state.")
            if not subgraph_error:
                 state['error_message'] = ((state.get('error_message') or '') + " StrategyAgent: No report generated.").strip()
    else:
        if not state.get('error_message'): # Don't overwrite specific exception message
             state['error_message'] = ((state.get('error_message') or '') + " StrategyAgent: Subgraph invocation failed critically.").strip()

    # Merge metadata from subgraph back to parent state
    if subgraph_final_state and subgraph_final_state.get("metadata") is not None: # Check if metadata exists and is not None
        state['metadata'] = subgraph_final_state.get("metadata") # Assign the list from subgraph
        # print(f"[StrategyAgentWrapper] Updated parent metadata to: {state['metadata']}")
    # If subgraph_final_state.get("metadata") is None, the parent's metadata (which was copied) remains unchanged in the parent.
    # If the subgraph intended to clear metadata, it should return an empty list.

    # 4. Set next agent in parent graph
    print("[StrategyAgentWrapper] Setting next agent to ProfileAggregatorAgent.")
    state['next_agent_to_call'] = "ProfileAggregatorAgent"

    return state
