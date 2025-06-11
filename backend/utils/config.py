from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv()

class LLMProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"

class SearchProvider(str, Enum):
    DUCKDUCKGO = "duckduckgo"
    SERPAPI = "serpapi"
    TAVILY = "tavily"

class LLMConfig(BaseModel):
    provider: LLMProvider = Field(default=LLMProvider.GEMINI)
    openai_model: str = Field(default="gpt-4.1-nano")
    gemini_model: str = Field(default="gemini-1.5-flash")

class SearchConfig(BaseModel):
    provider: SearchProvider = Field(default=SearchProvider.DUCKDUCKGO)
    max_results: int = Field(default=3, ge=1, le=10)

class Config(BaseModel):
    # API Keys
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    gemini_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    duckduckgo_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("DUCKDUCKGO_API_KEY"))
    serpapi_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("SERPAPI_API_KEY"))
    tavily_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))
    
    # LLM Configuration
    llm: LLMConfig = Field(default_factory=LLMConfig)
    
    # Search Configuration
    search: SearchConfig = Field(default_factory=SearchConfig)
    
    # Additional settings
    debug_mode: bool = Field(default=False)
    cache_enabled: bool = Field(default=True)
    cache_ttl: int = Field(default=3600, ge=0)

    def get_current_llm_model(self) -> str:
        return self.llm.openai_model if self.llm.provider == LLMProvider.OPENAI else self.llm.gemini_model

    def update_from_dict(self, update_dict: Dict[str, Any]) -> None:
        for key, value in update_dict.items():
            if hasattr(self, key):
                if key == 'llm' and isinstance(value, dict):
                    self.llm = LLMConfig(**value)
                elif key == 'search' and isinstance(value, dict):
                    self.search = SearchConfig(**value)
                else:
                    setattr(self, key, value)

    def validate_api_keys(self) -> Dict[str, bool]:
        return {
            "openai": bool(self.openai_api_key) if self.llm.provider == LLMProvider.OPENAI else True,
            "gemini": bool(self.gemini_api_key) if self.llm.provider == LLMProvider.GEMINI else True,
            "search": {
                SearchProvider.DUCKDUCKGO: bool(self.duckduckgo_api_key),
                SearchProvider.SERPAPI: bool(self.serpapi_api_key),
                SearchProvider.TAVILY: bool(self.tavily_api_key),
            }.get(self.search.provider, False)
        }

config = Config()

# Legacy exports for backward compatibility
OPENAI_API_KEY = config.openai_api_key
GEMINI_API_KEY = config.gemini_api_key
DUCKDUCKGO_API_KEY = config.duckduckgo_api_key
SERPAPI_API_KEY = config.serpapi_api_key
TAVILY_API_KEY = config.tavily_api_key
