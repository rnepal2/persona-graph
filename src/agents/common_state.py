# src/agents/common_state.py
from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    leader_initial_input: str
    leadership_info: Optional[List[str]]
    reputation_info: Optional[List[str]]
    strategy_info: Optional[List[str]]
    aggregated_profile: Optional[str]
    error_message: Optional[str]
    next_agent_to_call: Optional[str]
