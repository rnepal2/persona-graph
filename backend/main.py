# src/main.py
import asyncio
from src.graph import app
from src.agents import AgentState

if __name__ == "__main__":
    print("Starting PersonaGraph execution...")
    initial_input: AgentState = {
        "leader_initial_input": "https://www.linkedin.com/in/exampleleader",
        "leadership_info": None,
        "reputation_info": None,
        "strategy_info": None,
        "background_info": None,
        "aggregated_profile": None,
        "error_message": None,
        "next_agent_to_call": None, 
        "metadata": [{"source": "main_initial", "data": "test_value"}]
    }

    print(f"Initial state being passed to the graph: {initial_input}")
    final_state = asyncio.run(app.ainvoke(initial_input))

    print("\n--- PersonaGraph Execution Finished ---")
    print("Final State:")
    for key, value in final_state.items():
        print(f"  {key}: {value}")

    # Verification
    if final_state.get("leadership_info"):
        print(f"\nLeadership Info Collected: {final_state['leadership_info']}")
    if final_state.get("reputation_info"):
        print(f"\nReputation Info Collected: {final_state['reputation_info']}")
    if final_state.get("strategy_info"):
        print(f"\nStrategy Info Collected: {final_state['strategy_info']}")
    if final_state.get("aggregated_profile"):
        print(f"\nAggregated Profile: {final_state['aggregated_profile']}")

    if final_state.get("error_message"):
        print(f"\nError during execution: {final_state['error_message']}")

    print("\nDone.")
