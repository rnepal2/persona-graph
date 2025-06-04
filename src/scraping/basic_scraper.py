# src/scraping_utils.py
from bs4 import BeautifulSoup
from typing import Optional
import aiohttp
import asyncio

USER_AGENT_HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

async def fetch_and_parse_url(url: str) -> Optional[str]:
    """
    Asynchronously fetches the content of a URL, parses it using BeautifulSoup, and extracts text.

    Args:
        url: The URL to fetch and parse.

    Returns:
        The extracted text content from the URL's body, or None if an error occurs.
    """
    print(f"Attempting to fetch URL: {url}")
    try:
        async with aiohttp.ClientSession(headers=USER_AGENT_HEADER) as session:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    print(f"Successfully fetched URL: {url} with status code {response.status}")
                    try:
                        content = await response.read()
                        soup = BeautifulSoup(content, 'html.parser')
                        # Extract text from the body; if body is None, use the whole document
                        if soup.body:
                            extracted_text = soup.body.get_text(separator=' ', strip=True)
                        else: # Fallback for pages that might not have a body tag or where it's empty
                            extracted_text = soup.get_text(separator=' ', strip=True)
                        
                        if not extracted_text.strip(): # Check if extracted text is empty or just whitespace
                            print(f"Warning: No text extracted from URL: {url}. Body might be empty or script-driven.")
                            # Depending on requirements, one might return None here or the (empty) extracted_text
                        
                        return extracted_text
                    except Exception as e:
                        print(f"Error parsing HTML content from URL {url}: {e}")
                        return None
                else:
                    print(f"Error fetching URL {url}: Status code {response.status}")
                    return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching {url}: {e}")
        return None

if __name__ == "__main__":
    print("Testing scraping_utils.py...")
    import asyncio
    # Test with a valid URL
    valid_url = "https://github.com/rnepal2"
    print(f"\n--- Testing with valid URL: {valid_url} ---")
    content = asyncio.run(fetch_and_parse_url(valid_url))
    if content:
        print(f"\nSuccessfully extracted content (first 500 chars):\n'{content[:500]}...'")
    else:
        print("\nFailed to extract content from the valid URL.")

    # Test with a known problematic/non-existent URL
    invalid_url = "http://thisshouldnotexist12345.com"
    print(f"\n--- Testing with invalid URL: {invalid_url} ---")
    content_invalid = asyncio.run(fetch_and_parse_url(invalid_url))
    if content_invalid:
        print(f"\nExtracted content from invalid URL (should not happen):\n'{content_invalid[:200]}...'")
    else:
        print("\nCorrectly failed to extract content from the invalid URL (or returned None).")
    
    # Test with a URL that might return non-200 status
    error_status_url = "https://httpstat.us/404" # This URL returns a 404 status
    print(f"\n--- Testing with URL that returns 404: {error_status_url} ---")
    content_error_status = asyncio.run(fetch_and_parse_url(error_status_url))
    if content_error_status:
         print(f"\nExtracted content from 404 URL (should ideally be None or minimal error page text):\n'{content_error_status[:200]}...'")
    else:
        print("\nCorrectly handled non-200 status for URL (returned None or error handled).")

    print("\nscraping_utils.py test finished.")
