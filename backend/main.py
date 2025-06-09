# src/main.py
import asyncio
import nest_asyncio
from multiprocessing import freeze_support
from src.graph import app
from src.agents import AgentState
import sys

# Apply nest_asyncio to handle nested event loops
nest_asyncio.apply()

# Set event loop policy for Windows to support Playwright subprocesses
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def main():
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
    return final_state

if __name__ == "__main__":
    # This is required for multiprocessing on Windows
    freeze_support()
    main()
