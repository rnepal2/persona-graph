# src/agents/leadership_agent.py
from typing import TypedDict, List, Optional, Dict, Any # Ensure Any is imported
from langgraph.graph import StateGraph, END
from .common_state import AgentState # This will eventually be removed or changed when LeadershipAgent becomes a subgraph
from src.utils.llm_utils import get_openai_response # Added import
from src.utils.models import SearchResultItem # Added import

# Define the internal state for the Leadership Agent subgraph
from src.utils.filter_utils import filter_search_results_logic, DEFAULT_BLOCKED_DOMAINS # Added import

class LeadershipAgentState(TypedDict):
    input_profile_summary: str
    generated_queries: Optional[List[str]]
    search_results: Optional[List[SearchResultItem]] # Updated type hint
    scraped_data: Optional[List[str]]
    leadership_report: Optional[str]
    error_message: Optional[str]
    metadata: Optional[List[Dict[str, Any]]] # New field

# Placeholder Internal Nodes for LeadershipAgent Subgraph
async def generate_leadership_queries_node(state: LeadershipAgentState) -> LeadershipAgentState:
    print("[LeadershipAgent] Generating leadership queries via LLM...")

    profile_summary = state.get("input_profile_summary", "No profile summary provided.")
    profile_name_placeholder = "the individual" # Or derive from summary

    system_prompt = """
You are an expert research analyst specializing in executive leadership. Your task is to create search queries that will identify content related to a leader's style, decision-making processes, and team interactions.
            """
    user_prompt = f"""
Generate 3-5 distinct search queries to find information about the leadership qualities and style of {profile_name_placeholder}. Their current profile summary is: "{profile_summary}". Focus on queries that would find:
1. Descriptions of their leadership style or management philosophy (e.g., articles, interviews).
2. Examples of significant decisions they made and the reported outcomes.
3. Information about their team building, mentorship, or communication style.
4. Quotes from them or about them regarding their leadership.

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
        print(f"[LeadershipAgent] LLM generated queries: {generated_queries}")
    else:
        print("[LeadershipAgent] LLM call failed or returned no response. Using default placeholder queries.")
        generated_queries = ["default leadership query 1", "default leadership query 2"]

    state['generated_queries'] = generated_queries
    return state

def execute_search_node(state: LeadershipAgentState) -> LeadershipAgentState:
    print("[LeadershipAgent] Executing search (placeholder)...")
    # Dummy results for LeadershipAgent
    dummy_results = [
        SearchResultItem(title="Jane Doe's Visionary Leadership at Innovate Inc.", link="http://businessnews.com/jane-doe-visionary", snippet="An article detailing Jane Doe's leadership style and strategic decisions.", source_api="placeholder_ldr"),
        SearchResultItem(title="Interview with Jane Doe on Team Building", link="http://leadershiptoday.com/jane-doe-interview", snippet="Jane Doe discusses her approach to team building and mentorship.", source_api="placeholder_ldr"),
        SearchResultItem(title="Jane Doe's Management Philosophy (LinkedIn Article)", link="http://linkedin.com/pulse/jane-doe-management", snippet="Jane Doe shares her thoughts on management on LinkedIn.", source_api="placeholder_ldr"), # Blocked domain
        SearchResultItem(title="Top 10 Recipes for Summer BBQs", link="http://foodblog.com/summer-bbq", snippet="Delicious recipes for your next barbecue.", source_api="placeholder_ldr"), # Irrelevant
        SearchResultItem(title="Critique of Innovate Inc.'s Recent Strategy", link="http://marketanalysis.com/innovate-critique", snippet="Analysis of Innovate Inc.'s strategy, mentioning Jane Doe's decisions.", source_api="placeholder_ldr")
    ]
    state['search_results'] = dummy_results
    return state

def scrape_results_node(state: LeadershipAgentState) -> LeadershipAgentState:
    print("[LeadershipAgent] Scraping results...")
    state['scraped_data'] = ["scraped content from url1"]
    return state

def analyze_data_node(state: LeadershipAgentState) -> LeadershipAgentState:
    print("[LeadershipAgent] Analyzing data...")
    # In a real scenario, this would involve an LLM call
    state['leadership_report'] = "Preliminary analysis: Leader seems proactive." # Placeholder
    return state

def compile_report_node(state: LeadershipAgentState) -> LeadershipAgentState:
    print("[LeadershipAgent] Compiling final report...")
    # This might refine the report from analyze_data_node
    state['leadership_report'] = (state.get('leadership_report', "") + " Final leadership report compiled.").strip()
    
    # Add metadata item
    if state.get('metadata') is None:
        state['metadata'] = []
    state['metadata'].append({"source": "LeadershipAgent", "info": "Leadership report generated"})
    print("[LeadershipAgent] Added item to its metadata.") # For logging
    return state

async def filter_search_results_node(state: LeadershipAgentState) -> LeadershipAgentState:
    agent_name = "LeadershipAgent"
    print(f"[{agent_name}] Filtering search results...")
    current_results = state.get('search_results') or []
    if not current_results:
        print(f"[{agent_name}] No search results to filter.")
        return state

    profile_summary = state.get('input_profile_summary', '')
    agent_specific_focus_description = "Leadership style, decision-making approaches, management philosophy, team interactions, and public commentary on leadership."

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
leadership_graph = StateGraph(LeadershipAgentState)

leadership_graph.add_node("generate_leadership_queries", generate_leadership_queries_node)
leadership_graph.add_node("execute_search", execute_search_node)
leadership_graph.add_node("filter_search_results", filter_search_results_node) # Added node
leadership_graph.add_node("scrape_results", scrape_results_node)
leadership_graph.add_node("analyze_data", analyze_data_node)
leadership_graph.add_node("compile_report", compile_report_node)

leadership_graph.set_entry_point("generate_leadership_queries")
leadership_graph.add_edge("generate_leadership_queries", "execute_search")
leadership_graph.add_edge("execute_search", "filter_search_results") # Changed edge
leadership_graph.add_edge("filter_search_results", "scrape_results") # Added edge
leadership_graph.add_edge("scrape_results", "analyze_data")
leadership_graph.add_edge("analyze_data", "compile_report")
leadership_graph.add_edge("compile_report", END)

leadership_subgraph_app = leadership_graph.compile()

# Wrapper node for the LeadershipAgent subgraph
async def leadership_agent_node(state: AgentState) -> AgentState: # Changed to async def
    print("[MainGraph] Calling LeadershipAgent subgraph...")

    # 1. Transform parent state to initial subgraph state
    parent_input = state.get("leader_initial_input")
    if parent_input is None:
        print("[LeadershipAgentWrapper] Warning: No leader_initial_input found in parent state.")
        # Option 1: Return early with error or default
        # state['error_message'] = "LeadershipAgent: Missing leader_initial_input"
        # state['next_agent_to_call'] = "ReputationAgent" # Or END, or a specific error handler node
        # return state
        # Option 2: Proceed with a default/empty input for the subgraph
        parent_input = "No specific profile input provided."


    # Ensure all required fields for LeadershipAgentState are initialized.
    # 'input_profile_summary' is the only required field without a default in LeadershipAgentState.
    # Optional fields will be None by default if not provided.
    initial_subgraph_state = LeadershipAgentState(
        input_profile_summary=parent_input,
        generated_queries=None, 
        search_results=None,
        scraped_data=None,
        leadership_report=None, 
        error_message=None,
        metadata=list(state.get('metadata') or []) # Pass a shallow copy
    )

    # 2. Invoke the subgraph
    # We might want to add a try-except block here if the subgraph invocation can fail
    subgraph_final_state: Optional[LeadershipAgentState] = None # Ensure it's defined for all paths
    try:
        print(f"[LeadershipAgentWrapper] Invoking subgraph with initial state: {{'input_profile_summary': '{parent_input[:50]}...'}}")
        # Note: Invoke expects a dict, TypedDict is a dict at runtime. Ensure it's a plain dict for invoke.
        subgraph_final_state = await leadership_subgraph_app.ainvoke(initial_subgraph_state) # Changed to await and ainvoke
        print(f"[LeadershipAgentWrapper] Subgraph finished. Final state: {subgraph_final_state}")
    except Exception as e:
        print(f"[LeadershipAgentWrapper] Error invoking subgraph: {e}")
        # Handle error: update parent state with error message
        state['error_message'] = ((state.get('error_message') or '') + f" LeadershipAgent failed: {e}").strip()
        # subgraph_final_state will remain None or be the partial state if the subgraph handles errors internally

    # 3. Transform subgraph result back to parent state
    if subgraph_final_state:
        report = subgraph_final_state.get("leadership_report")
        subgraph_error = subgraph_final_state.get("error_message")

        if subgraph_error:
            state['error_message'] = ((state.get('error_message') or '') + f" LeadershipSubgraphError: {subgraph_error}").strip()
            print(f"[LeadershipAgentWrapper] Subgraph reported an error: {subgraph_error}")


        if report:
            if state.get('leadership_info') is None:
                state['leadership_info'] = []
            # Ensure it's a list before appending
            if not isinstance(state.get('leadership_info'), list):
                 state['leadership_info'] = []
            state['leadership_info'].append(report) # Append report to list
        else:
            print("[LeadershipAgentWrapper] No report found in subgraph final state.")
            # Optionally add a placeholder if no report, or handle as error
            if not subgraph_error: # Avoid overwriting a more specific error
                 state['error_message'] = ((state.get('error_message') or '') + " LeadershipAgent: No report generated.").strip()

    else: # Handles case where subgraph_final_state itself is None due to an exception during invoke
        if not state.get('error_message'): # Don't overwrite specific exception message from invoke's except block
            state['error_message'] = ((state.get('error_message') or '') + " LeadershipAgent: Subgraph invocation failed critically or returned None.").strip()

        # Also handle metadata if subgraph_final_state is None
        # Though typically metadata wouldn't be generated if the subgraph fails critically
        # This ensures parent metadata isn't lost if it was intended to be modified even on failure by some logic (not current placeholder)

    # Merge metadata from subgraph back to parent state
    if subgraph_final_state and subgraph_final_state.get("metadata") is not None: # Check if metadata exists and is not None
        state['metadata'] = subgraph_final_state.get("metadata") # Assign the list from subgraph
        # print(f"[LeadershipAgentWrapper] Updated parent metadata to: {state['metadata']}")
    # If subgraph_final_state.get("metadata") is None, the parent's metadata (which was copied) remains unchanged in the parent.
    # If the subgraph intended to clear metadata, it should return an empty list.


    # 4. Set next agent in parent graph
    print("[LeadershipAgentWrapper] Setting next agent to ReputationAgent.")
    state['next_agent_to_call'] = "ReputationAgent"

    return state
