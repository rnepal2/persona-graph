# src/agents/common_state.py
from typing import TypedDict, List, Optional, Dict, Any # Ensure Any is imported

class AgentState(TypedDict):
    """
    State object passed between agents in the persona-graph pipeline.
    Fields:
        leader_initial_input: str - Initial input (e.g., LinkedIn URL or name).
        leadership_info: Optional[List[str]] - Extracted leadership-related info.
        reputation_info: Optional[List[str]] - Extracted reputation-related info.
        strategy_info: Optional[List[str]] - Extracted strategy/business info.
        background_info: Optional[Dict[str, Any]] - Background data (education, work, etc.).
        aggregated_profile: Optional[str] - Final compiled executive profile.
        error_message: Optional[str] - Error message if any agent fails.
        next_agent_to_call: Optional[str] - Name of the next agent for routing.
        metadata: Optional[List[Dict[str, Any]]] - Trace, provenance, or debug info for auditability.
        history: Optional[List[Dict[str, Any]]] - (Optional) Step-by-step trace of agent actions.
    """
    name: str
    leader_initial_input: str
    leadership_info: Optional[List[str]]
    reputation_info: Optional[List[str]]
    strategy_info: Optional[List[str]]    
    background_info: Optional[str]
    aggregated_profile: Optional[str]
    error_message: Optional[str]
    next_agent_to_call: Optional[str]
    metadata: Optional[List[Dict[str, Any]]]  
    history: Optional[List[Dict[str, Any]]]
