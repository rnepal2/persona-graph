# src/config.py
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DUCKDUCKGO_API_KEY = os.getenv("DUCKDUCKGO_API_KEY") # If DDG requires one, otherwise can be placeholder
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Add other configurations as needed
# For example:
# DEFAULT_LLM_MODEL_OPENAI = "gpt-4"
# DEFAULT_LLM_MODEL_GEMINI = "gemini-pro"
