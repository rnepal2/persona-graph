# src/agents/leadership_agent.py
from typing import TypedDict, List, Optional, Dict
from langgraph.graph import StateGraph, END
from .common_state import AgentState # This will eventually be removed or changed when LeadershipAgent becomes a subgraph

# Define the internal state for the Leadership Agent subgraph
class LeadershipAgentState(TypedDict):
    input_profile_summary: str
    generated_queries: Optional[List[str]]
    search_results: Optional[List[Dict[str, str]]] # Assuming search results are dicts with string values
    scraped_data: Optional[List[str]]
    leadership_report: Optional[str]
    error_message: Optional[str]

# Placeholder Internal Nodes for LeadershipAgent Subgraph
def generate_queries_node(state: LeadershipAgentState) -> LeadershipAgentState:
    print("[LeadershipAgent] Generating queries...")
    # Ensure the key exists and is initialized correctly if needed, or rely on TypedDict Optional for initial None
    state['generated_queries'] = ["placeholder query 1 for leader", "placeholder query 2 for leader"]
    return state

def execute_search_node(state: LeadershipAgentState) -> LeadershipAgentState:
    print("[LeadershipAgent] Executing search...")
    state['search_results'] = [{"title": "Result 1", "href": "url1", "body": "Snippet 1"}]
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
    return state

# Instantiate and Build the Subgraph
leadership_graph = StateGraph(LeadershipAgentState)

leadership_graph.add_node("generate_queries", generate_queries_node)
leadership_graph.add_node("execute_search", execute_search_node)
leadership_graph.add_node("scrape_results", scrape_results_node)
leadership_graph.add_node("analyze_data", analyze_data_node)
leadership_graph.add_node("compile_report", compile_report_node)

leadership_graph.set_entry_point("generate_queries")
leadership_graph.add_edge("generate_queries", "execute_search")
leadership_graph.add_edge("execute_search", "scrape_results")
leadership_graph.add_edge("scrape_results", "analyze_data")
leadership_graph.add_edge("analyze_data", "compile_report")
leadership_graph.add_edge("compile_report", END)

leadership_subgraph_app = leadership_graph.compile()

# Wrapper node for the LeadershipAgent subgraph
def leadership_agent_node(state: AgentState) -> AgentState:
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
        generated_queries=None, # Or pass if some pre-generated queries exist
        search_results=None,
        scraped_data=None,
        leadership_report=None,
        error_message=None
    )

    # 2. Invoke the subgraph
    # We might want to add a try-except block here if the subgraph invocation can fail
    subgraph_final_state: Optional[LeadershipAgentState] = None # Ensure it's defined for all paths
    try:
        print(f"[LeadershipAgentWrapper] Invoking subgraph with initial state: {{'input_profile_summary': '{parent_input[:50]}...'}}")
        # Note: Invoke expects a dict, TypedDict is a dict at runtime. Ensure it's a plain dict for invoke.
        subgraph_final_state = leadership_subgraph_app.invoke(initial_subgraph_state) # Pass TypedDict directly
        print(f"[LeadershipAgentWrapper] Subgraph finished. Final state: {subgraph_final_state}")
    except Exception as e:
        print(f"[LeadershipAgentWrapper] Error invoking subgraph: {e}")
        # Handle error: update parent state with error message
        state['error_message'] = f"LeadershipAgent failed: {e}"
        # subgraph_final_state will remain None or be the partial state if the subgraph handles errors internally

    # 3. Transform subgraph result back to parent state
    if subgraph_final_state:
        report = subgraph_final_state.get("leadership_report")
        subgraph_error = subgraph_final_state.get("error_message")

        if subgraph_error:
            state['error_message'] = (state.get('error_message', '') + f" LeadershipSubgraphError: {subgraph_error}").strip()
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
                 state['error_message'] = (state.get('error_message', '') + " LeadershipAgent: No report generated.").strip()

    else: # Handles case where subgraph_final_state itself is None due to an exception during invoke
        if not state.get('error_message'): # Don't overwrite specific exception message from invoke's except block
            state['error_message'] = (state.get('error_message', '') + " LeadershipAgent: Subgraph invocation failed critically or returned None.").strip()


    # 4. Set next agent in parent graph
    print("[LeadershipAgentWrapper] Setting next agent to ReputationAgent.")
    state['next_agent_to_call'] = "ReputationAgent"

    return state
