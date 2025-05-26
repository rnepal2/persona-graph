# src/agents/strategy_agent.py
from typing import TypedDict, List, Optional, Dict
from langgraph.graph import StateGraph, END
from .common_state import AgentState # For the wrapper node later

# Define the internal state for the Strategy Agent subgraph
class StrategyAgentState(TypedDict):
    input_profile_summary: str
    generated_queries: Optional[List[str]]
    search_results: Optional[List[Dict[str, str]]]
    scraped_data: Optional[List[str]]
    strategy_report: Optional[str]
    error_message: Optional[str]

# Placeholder Internal Nodes for StrategyAgent Subgraph
def generate_strategy_queries_node(state: StrategyAgentState) -> StrategyAgentState:
    print("[StrategyAgent] Generating queries for strategy...")
    state['generated_queries'] = ["placeholder query 1 for strategy", "placeholder query 2 for strategy"]
    return state

def execute_strategy_search_node(state: StrategyAgentState) -> StrategyAgentState:
    print("[StrategyAgent] Executing search for strategy...")
    state['search_results'] = [{"title": "Strategy Result 1", "href": "strat_url1", "body": "Strategy Snippet 1"}]
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

# Instantiate and Build the Subgraph
strategy_graph = StateGraph(StrategyAgentState)

strategy_graph.add_node("generate_queries", generate_strategy_queries_node)
strategy_graph.add_node("execute_search", execute_strategy_search_node)
strategy_graph.add_node("scrape_results", scrape_strategy_results_node)
strategy_graph.add_node("analyze_data", analyze_strategy_data_node)
strategy_graph.add_node("compile_report", compile_strategy_report_node)

strategy_graph.set_entry_point("generate_queries")
strategy_graph.add_edge("generate_queries", "execute_search")
strategy_graph.add_edge("execute_search", "scrape_results")
strategy_graph.add_edge("scrape_results", "analyze_data")
strategy_graph.add_edge("analyze_data", "compile_report")
strategy_graph.add_edge("compile_report", END)

strategy_subgraph_app = strategy_graph.compile()

# Wrapper node for the StrategyAgent subgraph
def strategy_agent_node(state: AgentState) -> AgentState:
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
        error_message=None
    )

    # 2. Invoke the subgraph
    try:
        print(f"[StrategyAgentWrapper] Invoking subgraph with initial state: {{'input_profile_summary': '{parent_input[:50]}...'}}")
        subgraph_final_state = strategy_subgraph_app.invoke(initial_subgraph_state)
        print(f"[StrategyAgentWrapper] Subgraph finished. Final state: {subgraph_final_state}")
    except Exception as e:
        print(f"[StrategyAgentWrapper] Error invoking subgraph: {e}")
        state['error_message'] = (state.get('error_message', '') + f" StrategyAgent failed: {e}").strip()
        subgraph_final_state = None

    # 3. Transform subgraph result back to parent state
    if subgraph_final_state:
        report = subgraph_final_state.get("strategy_report")
        subgraph_error = subgraph_final_state.get("error_message")

        if subgraph_error:
            state['error_message'] = (state.get('error_message', '') + f" StrategySubgraphError: {subgraph_error}").strip()
            print(f"[StrategyAgentWrapper] Subgraph reported an error: {subgraph_error}")

        if report:
            if state.get('strategy_info') is None:
                state['strategy_info'] = []
            state['strategy_info'].append(report)
        else:
            print("[StrategyAgentWrapper] No report found in subgraph final state.")
            if not subgraph_error:
                 state['error_message'] = (state.get('error_message', '') + " StrategyAgent: No report generated.").strip()
    else:
        if not state.get('error_message'): # Don't overwrite specific exception message
             state['error_message'] = (state.get('error_message', '') + " StrategyAgent: Subgraph invocation failed critically.").strip()


    # 4. Set next agent in parent graph
    print("[StrategyAgentWrapper] Setting next agent to ProfileAggregatorAgent.")
    state['next_agent_to_call'] = "ProfileAggregatorAgent"

    return state
