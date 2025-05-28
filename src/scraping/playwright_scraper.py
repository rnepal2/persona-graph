import asyncio
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

async def scrape_with_playwright(url: str, headless: bool = True) -> Optional[str]:
    """
    Scrapes a URL using Playwright to handle dynamic content.
    Attempts to handle basic cookie pop-ups.
    Returns the text content of the body, or None on error.
    """
    print(f"[PlaywrightScraper] Attempting to scrape URL: {url}")
    browser = None # Initialize for finally block

    try:
        async with async_playwright() as p:
            print("[PlaywrightScraper] Launching browser...")
            try:
                # Defaulting to Chromium. Others (firefox, webkit) can be specified.
                browser = await p.chromium.launch(headless=headless)
            except Exception as e:
                # This can happen if browser binaries are not installed (e.g., via playwright install)
                print(f"[PlaywrightScraper] Browser launch failed: {e}")
                print("[PlaywrightScraper] Consider running 'playwright install' or ensuring browser binaries are accessible.")
                return None
            
            page = await browser.new_page()
            print(f"[PlaywrightScraper] Navigating to {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000) # 30s timeout

            # Basic attempt to accept cookies (very heuristic)
            cookie_buttons_selectors = [
                "button:has-text('accept all')",
                "button:has-text('allow all')",
                "button:has-text('agree')",
                "button:has-text('got it')",
                "button:has-text('i understand')",
                "div:has-text('accept cookies')",
                "#onetrust-accept-btn-handler" # Common ID
            ]
            for selector in cookie_buttons_selectors:
                try:
                    print(f"[PlaywrightScraper] Trying cookie button selector: {selector}")
                    button = page.locator(selector).first # .first to avoid issues if multiple match
                    await button.click(timeout=5000) # 5s timeout for click
                    print(f"[PlaywrightScraper] Clicked potential cookie button with selector: {selector}")
                    await asyncio.sleep(2) # Give time for overlay
                    break 
                except PlaywrightTimeoutError:
                    print(f"[PlaywrightScraper] Timeout clicking cookie button: {selector}")
                except Exception:
                    # print(f"[PlaywrightScraper] Cookie button not found or other error with selector: {selector}")
                    pass # Button not found or other error

            # Wait for page body to be present, or a specific main content element
            print("[PlaywrightScraper] Waiting for page content to load...")
            await page.wait_for_selector("body", timeout=15000) # 15s timeout

            # Extract text content - Playwright can often get text directly
            # Try to get main content, otherwise fall back to body
            main_content_element = page.locator("main").first or page.locator("article").first or page.locator("body")
            
            if await main_content_element.count() > 0: # Check if element exists
                text_content = await main_content_element.inner_text()
                # Replace multiple newlines/spaces resulting from .inner_text() on complex structures
                if text_content:
                     text_content = "\n".join([line.strip() for line in text_content.splitlines() if line.strip()])
            else:
                text_content = "" # Should not happen if body is present

            print(f"[PlaywrightScraper] Successfully extracted content. Length: {len(text_content)} chars.")
            return text_content

    except PlaywrightTimeoutError as pte:
        print(f"[PlaywrightScraper] Playwright timeout error during scraping {url}: {pte}")
        return None
    except Exception as e:
        print(f"[PlaywrightScraper] Error during Playwright scraping for {url}: {e}")
        return None
    finally:
        if browser:
            print("[PlaywrightScraper] Closing browser.")
            await browser.close()

if __name__ == '__main__':
    async def main_test_playwright():
        # Test with a site known for dynamic content or cookie banners.
        # test_url = "https://www.example.com"
        test_url = "http://web-scraping.dev/dynamic" # A site designed for testing, might not be live

        print(f"Attempting to scrape (Playwright): {test_url}")
        # In a restricted environment, browser setup via 'playwright install' might be needed.
        content = await scrape_with_playwright(test_url)
        if content:
            print(f"Successfully scraped content (first 500 chars):\n{content[:500]}")
        else:
            print(f"Failed to scrape content from {test_url} using Playwright (may need 'playwright install' or URL is down).")

    asyncio.run(main_test_playwright())
