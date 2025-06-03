# src/llm_utils.py
import asyncio
from typing import Optional
from utils.config import OPENAI_API_KEY, GEMINI_API_KEY

try:
    from openai import AsyncOpenAI, APIError as OpenAIApiError
except ImportError:
    try:
        import openai
        AsyncOpenAI = openai.AsyncOpenAI
        OpenAIApiError = openai.APIError
    except ImportError:
        print("Warning: OpenAI library not installed. pip install openai")
        AsyncOpenAI = None 
        OpenAIApiError = None

async def get_openai_response(prompt: str, system_prompt: Optional[str] = None, model_name: str = "gpt-3.5-turbo") -> Optional[str]:
    """
    Gets an asynchronous response from the OpenAI API.

    Args:
        prompt: The user prompt to send to the LLM.
        system_prompt: An optional system-level prompt to guide the LLM's behavior.
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
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        print(f"Sending prompt asynchronously to OpenAI model {model_name}...")
        response = await client.chat.completions.create( # Use await
            model=model_name,
            messages=messages
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

try:
    import google.generativeai as genai
except ImportError:
    print("Warning: Google Generative AI library not installed. pip install google-generativeai")
    genai = None

async def get_gemini_response(prompt: str, model_name: str = "gemini-2.0-flash") -> Optional[str]:
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
        response = await model.generate_content_async(prompt)
        if response.parts:
            return response.text
        elif hasattr(response, 'text'):
             return response.text
        else:
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
    
    test_user_prompt = "Explain the concept of a Large Language Model in one sentence."
    test_system_prompt = "You are a helpful AI assistant."
    print(f"\nTest User Prompt: \"{test_user_prompt}\"")
    print(f"Test System Prompt: \"{test_system_prompt}\"")

    # Test OpenAI
    print("\n--- Testing OpenAI (async) ---")
    if OPENAI_API_KEY:
        print("OPENAI_API_KEY found. Attempting to get response...")
    else:
        print("OPENAI_API_KEY not found. Expecting warning from function.")
    
    openai_response = asyncio.run(get_openai_response(test_user_prompt, system_prompt=test_system_prompt))
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
        
    gemini_response = asyncio.run(get_gemini_response(prompt=test_user_prompt))
    if gemini_response:
        print(f"Gemini Response: {gemini_response}")
    else:
        print("No response from Gemini (or API key was missing/error occurred).")

    print("\nllm_utils.py (async) test finished.")
