# src/agents/strategy_agent.py
from typing import List, Optional
from .common_state import AgentState

def strategy_agent_node(state: AgentState) -> AgentState:
    print("[Strategy Agent Node] called.")
    updated_state = state.copy()
    if updated_state.get("strategy_info") is None:
        updated_state["strategy_info"] = [] # Initialize if None
    # Ensure it's a list before appending
    if not isinstance(updated_state.get("strategy_info"), list):
        updated_state["strategy_info"] = []
        
    updated_state["strategy_info"].append("Strategy info placeholder from StrategyAgent")
    updated_state["next_agent_to_call"] = "ProfileAggregatorAgent"
    return updated_state
