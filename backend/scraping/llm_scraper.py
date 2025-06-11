import asyncio
from typing import Optional, List
from utils.llm_utils import get_openai_response, get_gemini_response
HTML_TRUNCATION_LIMIT = 8000 # Characters

async def scrape_with_llm(
    html_content: str,
    url_for_context: Optional[str] = None,
    extraction_focus: Optional[str] = None # e.g., "the main article text or all content relaed to person X"
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
    prompt = f"{system_prompt}\n\n{user_prompt}"
    llm_extracted_text = await get_gemini_response(prompt=prompt, model_name="gpt-4.1-nano")

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
        extracted_content = await scrape_with_llm(sample_html_content, "http://example.com/test_page", "main article text")
        
        if extracted_content:
            print("\n--- Extracted Content: ---")
            print(extracted_content)
            print("--- End of Extracted Content ---")
        else:
            print("LLM Scraper did not return content (check API key if testing live, or if LLM determined no main content).")

    asyncio.run(main_test_llm_scraper())
