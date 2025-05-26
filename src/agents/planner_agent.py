# src/agents/planner_agent.py
from typing import List, Optional # Though not strictly needed for this specific node, good for consistency
from .common_state import AgentState

def planner_supervisor_node(state: AgentState) -> AgentState:
    print("[Planner/Supervisor Node] called.")
    # In a real scenario, this node would analyze input and decide the first agent.
    # For now, it just sets the first agent to call.
    updated_state = state.copy()
    updated_state["next_agent_to_call"] = "LeadershipAgent"
    return updated_state
