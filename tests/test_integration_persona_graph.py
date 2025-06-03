# tests/test_integration_persona_graph.py
"""
Integration test for the persona-graph pipeline.
This test runs the main pipeline with a test input and checks that all major fields are populated in the final state.
"""
import asyncio
import sys
import os

# Ensure src is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from graph import app
from agents.common_state import AgentState

def test_persona_graph_pipeline():
    initial_input: AgentState = {
        "leader_initial_input": "https://www.linkedin.com/in/nepalrabindra",
        "leadership_info": None,
        "reputation_info": None,
        "strategy_info": None,
        "background_info": None,
        "aggregated_profile": None,
        "error_message": None,
        "next_agent_to_call": None,
        "metadata": [{"source": "test_case", "data": "test_value"}],
        "history": None
    }
    final_state = asyncio.run(app.ainvoke(initial_input))
    print("\n--- PersonaGraph Integration Test Output ---")
    for key, value in final_state.items():
        print(f"  {key}: {value}")
    # Assert that all major fields are present and not None (except error_message)
    assert final_state["background_info"] is not None, "Background info missing"
    assert final_state["leadership_info"] is not None, "Leadership info missing"
    assert final_state["reputation_info"] is not None, "Reputation info missing"
    assert final_state["strategy_info"] is not None, "Strategy info missing"
    assert final_state["aggregated_profile"] is not None, "Aggregated profile missing"
    assert final_state["error_message"] is None, f"Error occurred: {final_state['error_message']}"

if __name__ == "__main__":
    test_persona_graph_pipeline()
    print("\nIntegration test passed.")
