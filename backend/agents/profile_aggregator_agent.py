# src/agents/profile_aggregator_agent.py
from typing import List, Optional
from agents.common_state import AgentState
from utils.llm_utils import get_gemini_response

async def get_aggregated_profile(state: AgentState) -> str:
    name = state.get("name", "Executive Name")
    background = state.get("background_info", "")
    leadership = state.get("leadership_info", "")
    reputation = state.get("reputation_info", "")
    strategy = state.get("strategy_info", "")

    context = f"Name: {name}\n\n"
    
    if background:
        context += f"Background Information:\n{background}\n\n"
    if leadership:
        context += f"Leadership Analysis:\n{leadership}\n\n"
    if reputation:
        context += f"Reputation Assessment:\n{reputation}\n\n"
    if strategy:
        context += f"Strategic Analysis:\n{strategy}\n\n"

    prompt = f"""You are an expert executive profile compiler. You are given with information 
    collected from extensive web searches by AI agents for an executive/professional. Based on only the provided
    information, create a comprehensive executive profile. The profile should be completely fact-based
    on only provided information, and should not include any assumptions or opinions. It should be 
    appropriately structured and formatted, based on the available information for the profile.

    Remember, don't try to make up any information, or section when information not available. Your task 
    is not to complete the profile of the executive, but to aggregate the information provided and present 
    it in a structured manner that is informative, well-organized, and easy to read. The concatenated
    form of all collected relevant information for the executive is provided below:\n

    {context}
    """
    response = await get_gemini_response(prompt, model_name="gemini-2.0-flash")
    if response:
        return response.strip()
    return "No aggregated profile could be created!"

async def profile_aggregator_node(state: AgentState) -> AgentState:
    print(">>>[Profile Aggregator Node] called.")
    
    # Check what data we have available
    has_background = state.get("background_info") is not None
    has_leadership = state.get("leadership_info") is not None
    has_reputation = state.get("reputation_info") is not None
    has_strategy = state.get("strategy_info") is not None
    
    print(f"[Profile Aggregator] Available info - Background: {has_background}, Leadership: {has_leadership}, Reputation: {has_reputation}, Strategy: {has_strategy}")
    
    # Wait for parallel agents to complete if we're in streaming mode
    if not (has_leadership and has_reputation and has_strategy):
        print("[Profile Aggregator] Waiting for parallel agents to complete...")
        import asyncio
        await asyncio.sleep(1)  # Brief wait
        
        # Re-check after waiting
        has_leadership = state.get("leadership_info") is not None
        has_reputation = state.get("reputation_info") is not None
        has_strategy = state.get("strategy_info") is not None
        
        print(f"[Profile Aggregator] After wait - Leadership: {has_leadership}, Reputation: {has_reputation}, Strategy: {has_strategy}")
    
    # Generate profile with whatever data we have
    updated_state = state.copy()
    updated_state["aggregated_profile"] = await get_aggregated_profile(updated_state)
    updated_state["next_agent_to_call"] = None
    
    # Ensure metadata is properly initialized and collect references
    if updated_state.get('metadata') is None:
        updated_state['metadata'] = []
    
    # Collect all references from metadata
    all_refs = []
    for m in updated_state['metadata']:
        if isinstance(m, dict):
            for k, v in m.items():
                if k.endswith('_references') and isinstance(v, list):
                    all_refs.extend(v)
    
    # Add aggregation metadata
    updated_state['metadata'].append({
        'agent': 'ProfileAggregator',
        'all_references': all_refs,
        'aggregation_completed': True
    })
    
    print(f"[Profile Aggregator] Generated profile of length: {len(updated_state.get('aggregated_profile', ''))}")
    return updated_state
