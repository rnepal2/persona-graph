# src/agents/common_state.py
from typing import TypedDict, List, Optional, Dict, Any # Ensure Any is imported

class AgentState(TypedDict):
    leader_initial_input: str
    leadership_info: Optional[List[str]]
    reputation_info: Optional[List[str]]
    strategy_info: Optional[List[str]]
    background_info: Optional[Dict[str, Any]] # New field for BackgroundAgent's output
    aggregated_profile: Optional[str]
    error_message: Optional[str]
    next_agent_to_call: Optional[str]
    metadata: Optional[List[Dict[str, Any]]] # New field
