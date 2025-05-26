# src/llm_utils.py

import asyncio # Added for async
from typing import Optional

# Import API Keys from src.config
try:
    from src.config import OPENAI_API_KEY, GEMINI_API_KEY
    # Future enhancement:
    # from src.config import DEFAULT_LLM_MODEL_OPENAI, DEFAULT_LLM_MODEL_GEMINI
except ImportError:
    print("Warning: Could not import from src.config. API keys might not be available.")
    OPENAI_API_KEY = None
    GEMINI_API_KEY = None

# OpenAI Integration
try:
    # Try direct import first
    from openai import AsyncOpenAI, APIError as OpenAIApiError
except ImportError:
    try:
        # Fallback to importing openai and accessing via attribute
        import openai
        AsyncOpenAI = openai.AsyncOpenAI
        OpenAIApiError = openai.APIError # Assuming APIError is also accessible this way
    except ImportError:
        print("Warning: OpenAI library not installed. pip install openai")
        AsyncOpenAI = None # type: ignore
        OpenAIApiError = None # type: ignore

async def get_openai_response(prompt: str, model_name: str = "gpt-3.5-turbo") -> Optional[str]:
    """
    Gets an asynchronous response from the OpenAI API.

    Args:
        prompt: The prompt to send to the LLM.
        model_name: The OpenAI model name to use (e.g., "gpt-3.5-turbo", "gpt-4").

    Returns:
        The LLM's response text, or None if an error occurs or API key is missing.
    """
    if AsyncOpenAI is None or OpenAIApiError is None: # Check for AsyncOpenAI
        print("Error: OpenAI Async library components are not available. Cannot get OpenAI response.")
        return None

    if not OPENAI_API_KEY:
        print("Warning: OPENAI_API_KEY is not set. Cannot get OpenAI response.")
        return None

    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY) # Use AsyncOpenAI
        print(f"Sending prompt asynchronously to OpenAI model {model_name}...")
        response = await client.chat.completions.create( # Use await
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content
        else:
            print("Error: OpenAI response structure is unexpected or empty.")
            return None
    except OpenAIApiError as e: # Assuming OpenAIApiError is the correct async error type
        print(f"OpenAI API Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred with OpenAI: {e}")
        return None

# Gemini Integration
try:
    import google.generativeai as genai
except ImportError:
    print("Warning: Google Generative AI library not installed. pip install google-generativeai")
    genai = None # type: ignore

async def get_gemini_response(prompt: str, model_name: str = "gemini-pro") -> Optional[str]:
    """
    Gets an asynchronous response from the Google Gemini API.

    Args:
        prompt: The prompt to send to the LLM.
        model_name: The Gemini model name to use (e.g., "gemini-pro").

    Returns:
        The LLM's response text, or None if an error occurs or API key is missing.
    """
    if genai is None:
        print("Error: Google Generative AI library is not available. Cannot get Gemini response.")
        return None
        
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY is not set. Cannot get Gemini response.")
        return None

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(model_name)
        print(f"Sending prompt asynchronously to Gemini model {model_name}...")
        response = await model.generate_content_async(prompt) # Use await and generate_content_async
        # Check if parts are available and then text
        if response.parts:
            return response.text # response.text is a shortcut for response.parts[0].text
        elif hasattr(response, 'text'): # Fallback if .text is directly available but parts might be empty
             return response.text
        else:
            # If the response itself is the candidate (older API versions or specific error messages)
            # It might be helpful to log the full response candidate for debugging
            # print(f"Full Gemini response candidate: {response.candidates}")
            # Check for safety ratings or blocks
            if response.prompt_feedbacks:
                for feedback in response.prompt_feedbacks:
                    if feedback.block_reason:
                        print(f"Gemini content generation blocked. Reason: {feedback.block_reason_message or feedback.block_reason}")
                        return f"Content generation blocked: {feedback.block_reason_message or feedback.block_reason}"
            print("Error: Gemini response structure is unexpected or empty. No parts found and no direct text attribute.")
            return None

    except Exception as e:
        print(f"An unexpected error occurred with Gemini: {e}")
        return None

if __name__ == "__main__":
    print("Testing llm_utils.py (async)...")
    
    test_prompt = "Explain the concept of a Large Language Model in one sentence."
    print(f"\nTest Prompt: \"{test_prompt}\"")

    # Test OpenAI
    print("\n--- Testing OpenAI (async) ---")
    if OPENAI_API_KEY:
        print("OPENAI_API_KEY found. Attempting to get response...")
    else:
        print("OPENAI_API_KEY not found. Expecting warning from function.")
    
    openai_response = asyncio.run(get_openai_response(test_prompt))
    if openai_response:
        print(f"OpenAI Response: {openai_response}")
    else:
        print("No response from OpenAI (or API key was missing/error occurred).")

    # Test Gemini
    print("\n--- Testing Gemini (async) ---")
    if GEMINI_API_KEY:
        print("GEMINI_API_KEY found. Attempting to get response...")
    else:
        print("GEMINI_API_KEY not found. Expecting warning from function.")
        
    gemini_response = asyncio.run(get_gemini_response(test_prompt))
    if gemini_response:
        print(f"Gemini Response: {gemini_response}")
    else:
        print("No response from Gemini (or API key was missing/error occurred).")

    print("\nllm_utils.py (async) test finished.")
