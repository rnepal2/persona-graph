# PersonaGraph: Executive Profile Enrichment Platform

PersonaGraph is a generative AI-powered solution for in-depth profile enrichment of senior professionals using information scraped from web search and advanced LLMs.

## Features
- Input basic executive information (name, title, company, summary, LinkedIn, etc.)
- Choose AI model (Google Gemini, OpenAI GPT) and search engine (DuckDuckGo, SerpAPI, Tavily)
- Automated, agentic backend pipeline using LangGraph and multiple specialized agents
- Modern React.js frontend (ShadCN UI, Tailwind CSS)
- Flask backend for API and orchestration
- Extensible for research, recruiting, and due diligence use cases

## Project Structure

```
/                # Project root
  /backend/      # Python backend (LangGraph, agents, scraping, utils)
  /public/       # React public assets (favicon, index.html, etc.)
  /src/          # React app source (App.js, components, etc.)
  package.json   # React app config
  requirements.txt # Python backend dependencies
  ...            # Other config and docs
```

## Getting Started

### 1. Backend (Python)
- Install dependencies: `pip install -r requirements.txt`
- Run the backend (Flask or main.py):
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

---
For more details, see the code and comments in each directory.
