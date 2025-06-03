# src/config.py
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DUCKDUCKGO_API_KEY = os.getenv("DUCKDUCKGO_API_KEY") # if required by DDG
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
