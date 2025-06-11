import os
import asyncio
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
try:
    from utils.config import config, LLMProvider
except:
    from config import config, LLMProvider

try:
    from openai import AsyncOpenAI, APIError as OpenAIApiError
except ImportError:
    try:
        import openai
        AsyncOpenAI = openai.AsyncOpenAI
        OpenAIApiError = openai.APIError
    except ImportError:
        AsyncOpenAI = OpenAIApiError = None

async def get_openai_response(prompt: str, model_name: str = "gpt-4.1-nano") -> Optional[str]:
    if AsyncOpenAI is None or OpenAIApiError is None or not config.openai_api_key:
        return None

    try:
        client = AsyncOpenAI(api_key=config.openai_api_key)
        print(f">>>[OpenAI] API call with model: {model_name}")
        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content
        return None
    except (OpenAIApiError, Exception) as e:
        print(f"OpenAI error: {e}")
        return None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

async def get_gemini_response(prompt: str, model_name: str = "gemini-1.5-flash") -> Optional[str]:
    if genai is None or not config.gemini_api_key:
        return None

    try:
        genai.configure(api_key=config.gemini_api_key)
        model = genai.GenerativeModel(model_name)
        print(f">>>[Gemini] API call with model: {model_name}")
        response = await model.generate_content_async(prompt)
        
        if response.parts:
            return response.text
        if hasattr(response, 'text'):
            return response.text
        if response.prompt_feedbacks:
            for feedback in response.prompt_feedbacks:
                if feedback.block_reason:
                    return f"Content generation blocked: {feedback.block_reason}"
        return None
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

llm_gemini = ChatGoogleGenerativeAI(
    model=config.llm.gemini_model,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

async def async_parse_structured_data(
    text: str,
    schema: Type[BaseModel],
    llm=llm_gemini
) -> BaseModel:
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Extract relevant information from text. Return null for unknown attributes."
        ),
        ("human", "{text}"),
    ])
    structured_llm = llm.with_structured_output(schema=schema)
    final_prompt = prompt.invoke({"text": text})
    return await structured_llm.ainvoke(final_prompt)

async def get_llm_response(prompt: str, model_name: Optional[str] = None) -> Optional[str]:
    if model_name is None:
        model_name = config.get_current_llm_model()
        
    if config.llm.provider == LLMProvider.OPENAI:
        return await get_openai_response(prompt, model_name)
    elif config.llm.provider == LLMProvider.GEMINI:
        return await get_gemini_response(prompt, model_name)
    return None
