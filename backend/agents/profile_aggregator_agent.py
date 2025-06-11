# src/agents/profile_aggregator_agent.py
from typing import List, Optional
from agents.common_state import AgentState
from utils.llm_utils import get_gemini_response

async def get_aggregated_profile(state: AgentState) -> str:
    name = state.get("name", "Executive Name")
    background = state.get("background_info", {})
    leadership = state.get("leadership_info", [])
    reputation = state.get("reputation_info", [])
    strategy = state.get("strategy_info", [])

    context = ""
    if background:
        if isinstance(background, dict):
            for key, value in background.items():
                if isinstance(value, list):
                    context += f"{key.capitalize()}: {', '.join(map(str, value))}. "
                else:
                    context += f"{key.capitalize()}: {value}. "
        else:
            context += f"Background: {background}."
    context = f"""Name: {name} \n\n{context}"""

    if leadership:
        context += f"Leadership Info: {', '.join(map(str, leadership))}. "
    if reputation:
        context += f"Reputation Info: {', '.join(map(str, reputation))}. "
    if strategy:
        context += f"Strategy Info: {', '.join(map(str, strategy))}. "
    context = str(context).strip()
    aggregator_prompt = f"""Given the following information, create a comprehensive 
    executive profile. Background Information: \n 
    {context}
    """
    response = await get_gemini_response(aggregator_prompt, model_name="gemini-1.5-flash")
    if response:
        return response.strip()
    return "No aggregated profile could be created!"

async def profile_aggregator_node(state: AgentState) -> AgentState:
    print(">>>[Profile Aggregator Node] called.")
    updated_state = state.copy()
    updated_state["aggregated_profile"] = await get_aggregated_profile(updated_state)
    updated_state["next_agent_to_call"] = None
    if updated_state.get('metadata') is None:
        updated_state['metadata'] = []
    all_refs = []
    for m in updated_state['metadata']:
        for k, v in m.items():
            if k.endswith('_references') and isinstance(v, list):
                all_refs.extend(v)
    updated_state['metadata'] = [m for m in updated_state['metadata'] if 'all_references' not in m]
    updated_state['metadata'].append({'all_references': all_refs})
    return updated_state
