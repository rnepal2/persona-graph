import asyncio
from typing import Optional, List # List might not be needed directly for this function's return
from utils.llm_utils import get_openai_response # Or your preferred LLM util

# Define a rough character limit for HTML to avoid excessive token usage.
# This is a simple truncation strategy. More complex chunking could be future work.
# Average token is ~4 chars. 16k context window for gpt-3.5-turbo is ~64k chars.
# Let's be conservative for typical web page boilerplate.
# A large news article might be 5k-15k characters of actual content. HTML is much larger.
# Let's try with a 100k character limit for the HTML string passed to the LLM.
# This is still very large and might hit token limits for cheaper/smaller models if not careful.
# For gpt-3.5-turbo, max tokens for model is 4096 or 16385. If we assume 1 char ~ 1 token (worst case for complex HTML),
# this is too large. Let's aim for something safer like 15000 char limit for HTML, expecting it to be ~4k tokens.
# This might still be too large for the *output* if the LLM extracts everything.
# The prompt itself also takes tokens.
# Let's be very conservative: 8000 character truncation for HTML.
HTML_TRUNCATION_LIMIT = 8000 # Characters

async def scrape_with_llm(
    html_content: str,
    url_for_context: Optional[str] = None,
    extraction_focus: Optional[str] = None # e.g., "the main article text"
) -> Optional[str]:
    """
    Uses an LLM to extract main textual content from HTML.
    Focuses on the "full text extraction" mode.
    """
    print(f"[LLMScraper] Attempting to extract content from HTML using LLM. Original HTML length: {len(html_content)} chars.")

    if len(html_content) > HTML_TRUNCATION_LIMIT:
        print(f"[LLMScraper] HTML content is too long ({len(html_content)} chars). Truncating to {HTML_TRUNCATION_LIMIT} chars.")
        html_content_to_send = html_content[:HTML_TRUNCATION_LIMIT]
    else:
        html_content_to_send = html_content

    system_prompt = """You are an expert web content extraction assistant. Your primary goal is to accurately 
                    extract the main textual content (e.g., article body, main information) from provided HTML, 
                    stripping away boilerplate like navigation menus, headers, footers, advertisements, and sidebars. 
                    Focus on readable, coherent text. If the HTML appears to be non-textual (e.g., an image page,
                    an error page with no clear article), respond with "NO_MAIN_CONTENT_FOUND".
                    """

    user_task_description = """Extract the main textual content from the HTML provided below. Remove all
    "navigation links, ads, footers, headers, and other boilerplate. Present the extracted text clearly."""

    if extraction_focus:
        user_task_description += f" Prioritize content relevant to: '{extraction_focus}'."


    user_prompt = f"""Source URL (for context, if available): 
                     {url_for_context or 'N/A'}     
                    Extraction Focus: {extraction_focus or 'N/A'}

                    HTML Content:
                    {html_content_to_send}

                    Task: 
                    {user_task_description}
                """
    
    print(f"[LLMScraper] Sending HTML (first 200 chars): '{html_content_to_send[:200]}...' to LLM for extraction.")
    # Using a higher max_tokens for the response, as extracted content can be lengthy.
    # This needs to be balanced with cost and model limits.
    # For gpt-3.5-turbo, typical output might be up to 4096 tokens.
    # The get_openai_response function was updated in Phase 5.1, Step 4 (overall turn 182) to include max_tokens as an optional parameter.
    # However, the llm_utils.py file itself does not currently reflect this change.
    # For now, I'll call it without max_tokens, assuming it will use the model's default max.
    # This needs to be reconciled later.
    # llm_extracted_text = await get_openai_response(user_prompt, system_prompt=system_prompt, max_tokens_response=2000) # Adjust max_tokens_response as needed
    llm_extracted_text = await get_openai_response(user_prompt, system_prompt=system_prompt)


    if llm_extracted_text and "NO_MAIN_CONTENT_FOUND" not in llm_extracted_text:
        print(f"[LLMScraper] Successfully extracted content using LLM. Length: {len(llm_extracted_text)}")
        return llm_extracted_text.strip()
    elif "NO_MAIN_CONTENT_FOUND" in (llm_extracted_text or ""):
        print("[LLMScraper] LLM indicated no main content found.")
        return None
    else:
        print("[LLMScraper] LLM call failed or returned no usable content.")
        return None

if __name__ == '__main__':
    async def main_test_llm_scraper():
        sample_html_content = """
        <html><head><title>Test Page</title></head>
        <body>
            <header><h1>My Site</h1><nav><a>Home</a> <a>About</a></nav></header>
            <main>
                <h2>Main Article Title</h2>
                <p>This is the first paragraph of the main content. It's very important.</p>
                <p>This is another paragraph, continuing the discussion.</p>
                <aside>This is a sidebar, should be ignored.</aside>
            </main>
            <footer><p>&copy; 2023 My Site</p></footer>
        </body></html>
        """
        print("Testing LLM Scraper with sample HTML...")
        # To truly test, OpenAI API key needs to be set in .env
        # Without it, get_openai_response will print a warning and return None.
        extracted_content = await scrape_with_llm(sample_html_content, "http://example.com/test_page", "main article text")
        
        if extracted_content:
            print("\n--- Extracted Content: ---")
            print(extracted_content)
            print("--- End of Extracted Content ---")
        else:
            print("LLM Scraper did not return content (check API key if testing live, or if LLM determined no main content).")

    asyncio.run(main_test_llm_scraper())
