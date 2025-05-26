# src/agents/leadership_agent.py
from typing import List, Optional # For AgentState definition consistency, though not directly used by this node for its own logic beyond state type hint
from .common_state import AgentState

def leadership_agent_node(state: AgentState) -> AgentState:
    print("[Leadership Agent Node] called.")
    updated_state = state.copy()
    if updated_state.get("leadership_info") is None:
        updated_state["leadership_info"] = [] # Initialize if None
    # Ensure it's a list before appending, though AgentState defines it as Optional[List[str]]
    # This check is more for robustness if state manipulation outside typing occurs.
    if not isinstance(updated_state.get("leadership_info"), list):
        updated_state["leadership_info"] = []
        
    updated_state["leadership_info"].append("Leadership info placeholder from LeadershipAgent")
    updated_state["next_agent_to_call"] = "ReputationAgent"
    return updated_state
