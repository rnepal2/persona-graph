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

# Apply nest_asyncio to handle nested event loops
nest_asyncio.apply()

# Instantiate the graph
graph = StateGraph(AgentState) # AgentState is now imported

# Add nodes
graph.add_node("planner_supervisor_node", planner_supervisor_node)
graph.add_node("background_agent_node", background_agent_node)
graph.add_node("leadership_agent_node", leadership_agent_node)
graph.add_node("reputation_agent_node", reputation_agent_node)
graph.add_node("strategy_agent_node", strategy_agent_node)
graph.add_node("profile_aggregator_node", profile_aggregator_node)

# Set entry point
graph.add_edge(START, "planner_supervisor_node")

# Conditional routing function
# AgentState for type hinting is imported from src.agents
def should_continue(state: AgentState) -> str:
    if state.get("error_message"):
        print("Error detected, routing to END.")
        return END
    
    next_agent = state.get("next_agent_to_call")
    print(f"Routing based on next_agent_to_call: {next_agent}")

    # Order: Planner -> Background -> Leadership -> Reputation -> Strategy -> Aggregator
    if next_agent == "BackgroundAgent":
        return "background_agent_node"
    elif next_agent == "LeadershipAgent":
        return "leadership_agent_node"
    elif next_agent == "ReputationAgent":
        return "reputation_agent_node"
    elif next_agent == "StrategyAgent":
        return "strategy_agent_node"
    elif next_agent == "ProfileAggregatorAgent":
        return "profile_aggregator_node"
    else: # Includes None or any other unexpected value, or if planner didn't set (should not happen)
        print(f"No specific valid next agent, or end of defined flow. Next agent: {next_agent}. Routing to END.")
        return END

# Add conditional edges
graph.add_conditional_edges(
    "planner_supervisor_node",
    should_continue,
)
# Add conditional edge for the new BackgroundAgent
graph.add_conditional_edges(
    "background_agent_node",
    should_continue,
)
graph.add_conditional_edges(
    "leadership_agent_node",
    should_continue,
)
graph.add_conditional_edges(
    "reputation_agent_node",
    should_continue,
)
graph.add_conditional_edges(
    "strategy_agent_node",
    should_continue,
)
# The profile_aggregator_node now directly leads to END.
graph.add_edge("profile_aggregator_node", END)


# Compile the graph
app = graph.compile()

print("LangGraph app compiled successfully.")
