from pydantic import BaseModel, HttpUrl, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class User(BaseModel):
    """Model for user data"""
    id: Optional[int] = None
    email: EmailStr
    name: Optional[str] = None
    password: Optional[str] = None  # Only used for registration/login
    created_at: Optional[datetime] = None

class ProfileAccess(BaseModel):
    """Model for profile access control"""
    user_id: int
    profile_id: int
    access_level: str = "read"  # read, write, admin
    created_at: Optional[datetime] = None

class SearchResultItem(BaseModel):
    title: str
    link: HttpUrl
    snippet: Optional[str] = None
    source_api: str  # e.g., "duckduckgo", "serpapi", "tavily"
    content: Optional[str] = None  # For Tavily or pre-scraped content
    raw_result: Optional[Dict[str, Any]] = None # To store the original API output

class ExecutiveProfile(BaseModel):
    """Model for storing executive profile data"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    name: str
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    executive_profile: Optional[str] = None
    professional_background: Optional[str] = None
    leadership_summary: Optional[str] = None
    reputation_summary: Optional[str] = None
    strategy_summary: Optional[str] = None
    references_data: Optional[Dict[str, Any]] = None
    version: Optional[int] = None
    is_latest: Optional[bool] = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Example usage (can be commented out or within an if __name__ == "__main__": block for testing)
if __name__ == '__main__':
    example_result = SearchResultItem(
        title="Example Search Result",
        link="http://example.com",
        snippet="This is an example snippet.",
        source_api="duckduckgo",
        raw_result={"original_field": "original_value"}
    )
    print(example_result.model_dump_json(indent=2))

    example_tavily = SearchResultItem(
        title="Tavily Example",
        link="http://example.com/tavily",
        snippet="Snippet from Tavily.",
        source_api="tavily",
        content="This is the pre-scraped content from Tavily."
    )
    print(example_tavily.model_dump_json(indent=2))

    example_profile = ExecutiveProfile(
        name="John Doe",
        company="Example Corp",
        title="CEO",
        linkedin_url="http://linkedin.com/in/johndoe",
        executive_profile="John is an experienced executive...",
        professional_background="Background details...",
        leadership_summary="Leadership style and achievements...",
        reputation_summary="Public and media reputation...",
        strategy_summary="Strategic vision and plans...",
        references_data={"ref1": "Reference 1", "ref2": "Reference 2"},
        created_at="2023-10-01",
        updated_at="2023-10-10"
    )
    print(example_profile.model_dump_json(indent=2))
