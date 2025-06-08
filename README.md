## PersonaGraph: Executive Profile Generator

PersonaGraph is a generative AI-powered platform for in-depth enrichment of executive and senior professional profiles. It leverages advanced web scraping, multi-agent orchestration, and large language models (LLMs) to deliver comprehensive, up-to-date leadership intelligence.

### What Does It Do?
PersonaGraph automates the process of gathering, synthesizing, and enriching executive profiles using public web data and AI. By inputting basic information (name, title, company, LinkedIn, etc.), users receive a detailed, AI-generated profile summary, leadership insights, and referenced background information—enabling faster, deeper, and more reliable executive research.

### Potential Use Cases
- **Recruiting for Senior Leadership:** Companies and executive search firms can proactively identify, vet, and compare candidates for C-level and other strategic roles.
- **Succession Planning:** Organizations can continuously monitor and plan for key leadership transitions, identifying potential internal and external successors.
- **Venture Capital & Private Equity:** VC/PE firms can rapidly assess leadership teams of target companies or startups for due diligence, investment, or partnership decisions.
- **Competitive & Market Intelligence:** Analysts can benchmark leadership teams across industries, track executive moves, and map talent networks.

## How the Agentic Solution Works
PersonaGraph uses an agentic backend built on LangGraph, where each major aspect of profile enrichment is handled by specialized agents (subgraphs). The system orchestrates these agents in a directed graph:
- **Background Agent:** Gathers and synthesizes professional history and education.
- **Leadership Agent:** Extracts and analyzes leadership style, experience, and impact.
- **Strategy Agent:** Surfaces strategic initiatives, vision, and business approach.
- **Reputation Agent:** Assesses public reputation, media presence, and sentiment.
- **Profile Aggregator:** Combines all agent outputs into a unified, referenced executive profile.

Agents use Playwright-based and LLM-powered scrapers to extract and process web data. The LangGraph setup enables modular, parallel, and extensible enrichment pipelines.

## UI (Frontend)
The frontend is a minimal React.js app (ShadCN UI, Tailwind CSS) for inputting executive details, selecting AI/search options, and viewing enriched profiles. It connects to the backend via WebSocket for real-time progress and results. 

## Getting Started
---
### 1. Backend (Python)
- Install dependencies: `pip install -r requirements.txt`
- Run the backend:
  ```
  cd backend
  python main.py
  ```

### 2. Frontend (React)
- Install dependencies: `npm install`
- Start the dev server:
  ```
  npm start
  ```
- Access the app at [http://localhost:3000](http://localhost:3000)

## Development Notes
- The frontend calls backend API endpoints for profile enrichment.
- Backend uses async agentic graph (LangGraph) for multi-step enrichment.
- For local development, you may need to set up CORS or use a proxy for API calls.

## License
MIT

