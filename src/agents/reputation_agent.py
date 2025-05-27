# src/agents/reputation_agent.py
from typing import TypedDict, List, Optional, Dict, Any # Ensure Any is imported
from langgraph.graph import StateGraph, END
from .common_state import AgentState # Assuming this will be needed by the wrapper later
from src.utils.llm_utils import get_openai_response # Added import
from src.utils.models import SearchResultItem # Added import

# Define the internal state for the Reputation Agent subgraph
from src.utils.filter_utils import filter_search_results_logic, DEFAULT_BLOCKED_DOMAINS # Added import

class ReputationAgentState(TypedDict):
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
    profile_name_placeholder = "the individual" # Or derive from summary

    system_prompt = """
You are a specialist in public reputation and media analysis. Your goal is to devise search queries that gather information on an executive's public image, media presence, and notable recognitions or controversies.
            """
    user_prompt = f"""
Generate 3-5 distinct search queries to assess the public reputation of {profile_name_placeholder}. Their current profile summary is: "{profile_summary}". Focus the queries on:
1. News articles, press releases, or official announcements mentioning them.
2. Awards, honors, or significant recognitions they have received.
3. Any public controversies, legal issues, or criticisms involving them or their companies during their tenure.
4. Their reputation within their specific industry or among peers.

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
        print(f"[ReputationAgent] LLM generated queries: {generated_queries}")
    else:
        print("[ReputationAgent] LLM call failed or returned no response. Using default placeholder queries.")
        generated_queries = ["default reputation query 1", "default reputation query 2"]

    state['generated_queries'] = generated_queries
    return state

def execute_reputation_search_node(state: ReputationAgentState) -> ReputationAgentState:
    print("[ReputationAgent] Executing search for reputation (placeholder)...")
    # Dummy results for ReputationAgent
    dummy_results = [
        SearchResultItem(title="Jane Doe Public Praise for Charity Work", link="http://charitytimes.com/jane-doe-award", snippet="Jane Doe recognized for her significant contributions to local charities.", source_api="placeholder_rep"),
        SearchResultItem(title="Controversy Over Innovate Inc. Environmental Impact", link="http://environmentnews.com/innovate-controversy", snippet="Innovate Inc., led by Jane Doe, faces criticism over environmental practices.", source_api="placeholder_rep"),
        SearchResultItem(title="Jane Doe's Facebook Page", link="http://facebook.com/janedoeofficial", snippet="Official Facebook page of Jane Doe.", source_api="placeholder_rep"), # Blocked domain
        SearchResultItem(title="Review of Jane Doe's Favorite Local Bakery", link="http://localfoodblog.com/bakery-review", snippet="A review of a bakery Jane Doe reportedly frequents.", source_api="placeholder_rep"), # Irrelevant
        SearchResultItem(title="Jane Doe on Twitter", link="http://twitter.com/janedoe", snippet="Jane Doe's tweets on various topics.", source_api="placeholder_rep") # Blocked domain
    ]
    state['search_results'] = dummy_results
    return state

def scrape_reputation_results_node(state: ReputationAgentState) -> ReputationAgentState:
    print("[ReputationAgent] Scraping reputation results...")
    state['scraped_data'] = ["scraped reputation content from rep_url1"]
    return state

def analyze_reputation_data_node(state: ReputationAgentState) -> ReputationAgentState:
    print("[ReputationAgent] Analyzing reputation data...")
    state['reputation_report'] = "Preliminary analysis: Leader's reputation seems positive." # Placeholder
    return state

def compile_reputation_report_node(state: ReputationAgentState) -> ReputationAgentState:
    print("[ReputationAgent] Compiling final reputation report...")
    state['reputation_report'] = (state.get('reputation_report', "") + " Final reputation report compiled.").strip()
    return state

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

# Instantiate and Build the Subgraph
reputation_graph = StateGraph(ReputationAgentState)

reputation_graph.add_node("generate_reputation_queries", generate_reputation_queries_node)
reputation_graph.add_node("execute_search", execute_reputation_search_node)
reputation_graph.add_node("filter_search_results", filter_search_results_node) # Added node
reputation_graph.add_node("scrape_results", scrape_reputation_results_node)
reputation_graph.add_node("analyze_data", analyze_reputation_data_node)
reputation_graph.add_node("compile_report", compile_reputation_report_node)

reputation_graph.set_entry_point("generate_reputation_queries")
reputation_graph.add_edge("generate_reputation_queries", "execute_search")
reputation_graph.add_edge("execute_search", "filter_search_results") # Changed edge
reputation_graph.add_edge("filter_search_results", "scrape_results") # Added edge
reputation_graph.add_edge("scrape_results", "analyze_data")
reputation_graph.add_edge("analyze_data", "compile_report")
reputation_graph.add_edge("compile_report", END)

reputation_subgraph_app = reputation_graph.compile()

# Wrapper node for the ReputationAgent subgraph
async def reputation_agent_node(state: AgentState) -> AgentState: # Changed to async def
    print("[MainGraph] Calling ReputationAgent subgraph...")

    # 1. Transform parent state to initial subgraph state
    parent_input = state.get("leader_initial_input")
    if parent_input is None:
        print("[ReputationAgentWrapper] Warning: No leader_initial_input found in parent state.")
        parent_input = "No specific profile input provided for reputation analysis." # Default

    initial_subgraph_state = ReputationAgentState(
        input_profile_summary=parent_input,
        generated_queries=None,
        search_results=None,
        scraped_data=None,
        reputation_report=None,
        error_message=None,
        metadata=list(state.get('metadata') or []) # Pass a shallow copy
    )

    # 2. Invoke the subgraph
    try:
        print(f"[ReputationAgentWrapper] Invoking subgraph with initial state: {{'input_profile_summary': '{parent_input[:50]}...'}}")
        subgraph_final_state = await reputation_subgraph_app.ainvoke(initial_subgraph_state) # Changed to await and ainvoke
        print(f"[ReputationAgentWrapper] Subgraph finished. Final state: {subgraph_final_state}")
    except Exception as e:
        print(f"[ReputationAgentWrapper] Error invoking subgraph: {e}")
        state['error_message'] = ((state.get('error_message') or '') + f" ReputationAgent failed: {e}").strip()
        subgraph_final_state = None

    # 3. Transform subgraph result back to parent state
    if subgraph_final_state:
        report = subgraph_final_state.get("reputation_report")
        subgraph_error = subgraph_final_state.get("error_message")

        if subgraph_error:
            state['error_message'] = ((state.get('error_message') or '') + f" ReputationSubgraphError: {subgraph_error}").strip()
            print(f"[ReputationAgentWrapper] Subgraph reported an error: {subgraph_error}")

        if report:
            if state.get('reputation_info') is None:
                state['reputation_info'] = []
            state['reputation_info'].append(report)
        else:
            print("[ReputationAgentWrapper] No report found in subgraph final state.")
            if not subgraph_error:
                 state['error_message'] = ((state.get('error_message') or '') + " ReputationAgent: No report generated.").strip()
    else:
        if not state.get('error_message'):
             state['error_message'] = ((state.get('error_message') or '') + " ReputationAgent: Subgraph invocation failed critically.").strip()

    # Merge metadata from subgraph back to parent state
    if subgraph_final_state and subgraph_final_state.get("metadata") is not None: # Check if metadata exists and is not None
        state['metadata'] = subgraph_final_state.get("metadata") # Assign the list from subgraph
        # print(f"[ReputationAgentWrapper] Updated parent metadata to: {state['metadata']}")
    # If subgraph_final_state.get("metadata") is None, the parent's metadata (which was copied) remains unchanged in the parent.
    # If the subgraph intended to clear metadata, it should return an empty list.

    # 4. Set next agent in parent graph
    print("[ReputationAgentWrapper] Setting next agent to StrategyAgent.")
    state['next_agent_to_call'] = "StrategyAgent"

    return state
