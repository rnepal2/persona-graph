# src/graph_structure.py
import nest_asyncio
from langgraph.graph import StateGraph, START, END
from agents import (
    AgentState,
    planner_supervisor_node,
    leadership_agent_node,
    reputation_agent_node,
    strategy_agent_node,
    background_agent_node,
    profile_aggregator_node
)

nest_asyncio.apply()

# Instantiate graph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("planner_supervisor_node", planner_supervisor_node)
graph.add_node("background_agent_node", background_agent_node)
graph.add_node("leadership_agent_node", leadership_agent_node)
graph.add_node("reputation_agent_node", reputation_agent_node)
graph.add_node("strategy_agent_node", strategy_agent_node)
graph.add_node("profile_aggregator_node", profile_aggregator_node)

# Set entry point
graph.add_edge(START, "planner_supervisor_node")

# Conditional routing with parallel execution support
def should_continue_from_planner(state: AgentState) -> str:
    if state.get("error_message"):
        print("Error detected from planner, routing to END.")
        return END
    return "background_agent_node"

def should_continue_from_background(state: AgentState) -> list:
    if state.get("error_message"):
        print("Error detected from background, routing to END.")
        return END
    
    # Fan out to parallel execution of three agents
    print("Background completed successfully, starting parallel execution of Leadership, Reputation, and Strategy agents")
    return ["leadership_agent_node", "reputation_agent_node", "strategy_agent_node"]

def should_continue_to_aggregator(state: AgentState) -> str:
    if state.get("error_message"):
        print("Error detected, routing to END.")
        return END
    
    # ALWAYS route to aggregator - let it decide if it has enough data
    print("Routing to profile aggregator...")
    return "profile_aggregator_node"

# Add conditional edges
graph.add_conditional_edges(
    "planner_supervisor_node",
    should_continue_from_planner,
)

graph.add_conditional_edges(
    "background_agent_node", 
    should_continue_from_background,
)

# Three parallel agents route to aggregator agent
graph.add_conditional_edges(
    "leadership_agent_node",
    should_continue_to_aggregator,
)
graph.add_conditional_edges(
    "reputation_agent_node", 
    should_continue_to_aggregator,
)
graph.add_conditional_edges(
    "strategy_agent_node",
    should_continue_to_aggregator,
)
graph.add_edge("profile_aggregator_node", END)
app = graph.compile()
print("LangGraph app compiled successfully with parallel execution support.")