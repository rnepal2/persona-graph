# src/llm_utils.py

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
    from openai import OpenAI, APIError as OpenAIApiError
except ImportError:
    print("Warning: OpenAI library not installed. pip install openai")
    OpenAI = None # type: ignore 
    OpenAIApiError = None # type: ignore

def get_openai_response(prompt: str, model_name: str = "gpt-3.5-turbo") -> Optional[str]:
    """
    Gets a response from the OpenAI API.

    Args:
        prompt: The prompt to send to the LLM.
        model_name: The OpenAI model name to use (e.g., "gpt-3.5-turbo", "gpt-4").

    Returns:
        The LLM's response text, or None if an error occurs or API key is missing.
    """
    if OpenAI is None or OpenAIApiError is None:
        print("Error: OpenAI library is not available. Cannot get OpenAI response.")
        return None

    if not OPENAI_API_KEY:
        print("Warning: OPENAI_API_KEY is not set. Cannot get OpenAI response.")
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        print(f"Sending prompt to OpenAI model {model_name}...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content
        else:
            print("Error: OpenAI response structure is unexpected or empty.")
            return None
    except OpenAIApiError as e:
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

def get_gemini_response(prompt: str, model_name: str = "gemini-pro") -> Optional[str]:
    """
    Gets a response from the Google Gemini API.

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
        print(f"Sending prompt to Gemini model {model_name}...")
        response = model.generate_content(prompt)
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
    print("Testing llm_utils.py...")
    
    test_prompt = "Explain the concept of a Large Language Model in one sentence."
    print(f"\nTest Prompt: \"{test_prompt}\"")

    # Test OpenAI
    print("\n--- Testing OpenAI ---")
    if OPENAI_API_KEY:
        print("OPENAI_API_KEY found. Attempting to get response...")
    else:
        print("OPENAI_API_KEY not found. Expecting warning from function.")
    
    openai_response = get_openai_response(test_prompt)
    if openai_response:
        print(f"OpenAI Response: {openai_response}")
    else:
        print("No response from OpenAI (or API key was missing/error occurred).")

    # Test Gemini
    print("\n--- Testing Gemini ---")
    if GEMINI_API_KEY:
        print("GEMINI_API_KEY found. Attempting to get response...")
    else:
        print("GEMINI_API_KEY not found. Expecting warning from function.")
        
    gemini_response = get_gemini_response(test_prompt)
    if gemini_response:
        print(f"Gemini Response: {gemini_response}")
    else:
        print("No response from Gemini (or API key was missing/error occurred).")

    print("\nllm_utils.py test finished.")
