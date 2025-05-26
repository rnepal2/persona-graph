# PersonaGraph

PersonaGraph is a generative AI-powered solution designed to build detailed professional profiles of senior-level leaders. It leverages multiple AI agents, web search capabilities, and Large Language Models (LLMs) to gather, analyze, and synthesize information from various sources.

## Project Overview

The goal of PersonaGraph is to automate and enhance the process of understanding a leader's professional background, achievements, leadership style, and public reputation. This can be valuable for companies during succession planning, executive search, or competitive analysis.

The system uses a multi-agent approach orchestrated by LangGraph:
*   **Planner/Supervisor Agent:** Manages the overall workflow based on initial input (e.g., LinkedIn profile).
*   **LeadershipAgent:** Focuses on aspects related to leadership style, roles, and responsibilities.
*   **ReputationAgent:** Gathers information about public perception, news, and media presence.
*   **StrategyAgent:** Investigates strategic decisions, business impact, and financial performance.
*   **ProfileAggregatorAgent:** Consolidates information from all agents to create a comprehensive profile.

## Tech Stack (Initial)

*   **LLMs:** OpenAI (GPT series), Google Gemini
*   **Search:** DuckDuckGo API (initially), potentially Google Cloud Search or other SERP APIs
*   **Web Scraping:** Custom solution using `requests` and `BeautifulSoup4`
*   **Agent Framework:** LangGraph
*   **Programming Language:** Python

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd persona-graph
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
    *   Create a `.env` file in the root directory by copying the `.env.example` file:
        ```bash
        cp .env.example .env
        ```
    *   Open the `.env` file and add your API keys for OpenAI, Gemini, and any other services.

## Initial Architecture Thoughts

*   The system will be event-driven, with agents passing messages or state updates via the LangGraph framework.
*   Each agent will have a clearly defined responsibility and set of tools (LLM prompts, search functions, scraping functions).
*   Configuration for API keys, model names, and other parameters will be managed in `src/config.py` and loaded from environment variables.
*   Utility modules will be created for common tasks like web search, web scraping, and LLM interactions to promote code reusability.

## Next Steps

Refer to the project plan and upcoming tasks. The immediate next steps involve setting up the basic LangGraph structure and implementing the core utility modules.
