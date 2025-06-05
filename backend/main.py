# src/main.py

import asyncio # Added for asyncio.run
from src.graph import app
from src.agents import AgentState

if __name__ == "__main__":
    print("Starting PersonaGraph execution...")

    # Initial input for the graph
    initial_input: AgentState = {
        "leader_initial_input": "https://www.linkedin.com/in/exampleleader",
        "leadership_info": None,
        "reputation_info": None,
        "strategy_info": None,
        "background_info": None, # Initialize new field in AgentState
        "aggregated_profile": None,
        "error_message": None,
        "next_agent_to_call": None, # Will be set by the planner/supervisor
        "metadata": [{"source": "main_initial", "data": "test_value"}] # Example initial metadata
    }

    print(f"Initial state being passed to the graph: {initial_input}")

    # Invoke the graph
    # The config for a stream is empty, but it's good practice to pass it.
    # stream_config = {"recursion_limit": 10} # Default is 25, 10 should be enough for this linear graph
    
    # final_state = app.invoke(initial_input, config=stream_config)
    # For now, let's use a simple invoke without explicit config unless needed
    # final_state = app.invoke(initial_input) # Synchronous invoke
    final_state = asyncio.run(app.ainvoke(initial_input)) # Asynchronous invoke


    print("\n--- PersonaGraph Execution Finished ---")
    print("Final State:")
    for key, value in final_state.items():
        print(f"  {key}: {value}")

    # Verification print statements (optional, but good for this stage)
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
