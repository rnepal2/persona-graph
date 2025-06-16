# src/agents/common_state.py
from typing import TypedDict, List, Optional, Dict, Any, Annotated
import operator

def merge_strings(left: str, right: str) -> str:
    """Custom reducer for string fields - keeps the first non-empty value"""
    if left and left.strip():
        return left
    return right if right and right.strip() else ""

def merge_optional_strings(left: Optional[str], right: Optional[str]) -> Optional[str]:
    """Custom reducer for optional string fields - keeps the first non-None value"""
    if left is not None:
        return left
    return right

class AgentState(TypedDict):
    # Fields that are set once and shouldn't change
    name: Annotated[str, merge_strings]
    leader_initial_input: Annotated[str, merge_strings]
    
    # Fields that are updated by parallel agents - each agent updates only their own field
    leadership_info: Annotated[Optional[str], merge_optional_strings]
    reputation_info: Annotated[Optional[str], merge_optional_strings]
    strategy_info: Annotated[Optional[str], merge_optional_strings]
    background_info: Annotated[Optional[str], merge_optional_strings]
    aggregated_profile: Annotated[Optional[str], merge_optional_strings]
    
    # Error handling field - could be updated by any agent
    error_message: Annotated[Optional[str], merge_optional_strings]
    
    # Navigation field - not used in parallel execution but keeping safe
    next_agent_to_call: Annotated[Optional[str], merge_optional_strings]
    
    # Metadata - gets appended by multiple agents
    metadata: Annotated[List[Dict[str, Any]], operator.add]
    
    # History field - optional, rarely used
    history: Annotated[Optional[List[Dict[str, Any]]], lambda left, right: right if right is not None else left]
