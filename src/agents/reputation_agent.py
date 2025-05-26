# src/agents/reputation_agent.py
from typing import List, Optional
from .common_state import AgentState

def reputation_agent_node(state: AgentState) -> AgentState:
    print("[Reputation Agent Node] called.")
    updated_state = state.copy()
    if updated_state.get("reputation_info") is None:
        updated_state["reputation_info"] = [] # Initialize if None
    # Ensure it's a list before appending
    if not isinstance(updated_state.get("reputation_info"), list):
        updated_state["reputation_info"] = []
        
    updated_state["reputation_info"].append("Reputation info placeholder from ReputationAgent")
    updated_state["next_agent_to_call"] = "StrategyAgent"
    return updated_state
