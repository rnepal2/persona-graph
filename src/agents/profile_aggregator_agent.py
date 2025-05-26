# src/agents/profile_aggregator_agent.py
from typing import List, Optional
from .common_state import AgentState

def profile_aggregator_node(state: AgentState) -> AgentState:
    print("[Profile Aggregator Node] called.")
    updated_state = state.copy()
    # In a real scenario, this node would aggregate all gathered info.
    # For now, it just sets a placeholder aggregated profile.
    updated_state["aggregated_profile"] = "Aggregated profile placeholder from ProfileAggregatorAgent"
    updated_state["next_agent_to_call"] = None # Signifies completion of data gathering
    return updated_state
