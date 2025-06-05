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
    browser = None

    try:
        async with async_playwright() as p:
            print("[PlaywrightScraper] Launching browser...")
            try:
                browser = await p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
            except Exception as e:
                print(f"[PlaywrightScraper] Browser launch failed: {e}")
                print("[PlaywrightScraper] Consider running 'playwright install' or ensuring browser binaries are accessible.")
                return None

            context = await browser.new_context(viewport={"width": 1280, "height": 800}, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
            page = await context.new_page()

            print(f"[PlaywrightScraper] Navigating to {url}...")
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
            except PlaywrightTimeoutError:
                print(f"[PlaywrightScraper] Timeout while loading page: {url}")
                return None

            # Handle cookie pop-ups
            cookie_buttons_selectors = [
                "button:has-text('accept all')",
                "button:has-text('allow all')",
                "button:has-text('agree')",
                "button:has-text('got it')",
                "button:has-text('i understand')",
                "div:has-text('accept cookies')",
                "#onetrust-accept-btn-handler"
            ]
            for selector in cookie_buttons_selectors:
                try:
                    button = page.locator(selector).first
                    if await button.is_visible():
                        await button.click(timeout=3000)
                        print(f"[PlaywrightScraper] Clicked cookie button: {selector}")
                        await asyncio.sleep(2)
                        break
                except Exception:
                    pass

            print("[PlaywrightScraper] Waiting for page content to load...")
            try:
                await page.wait_for_selector("body", timeout=15000)
            except PlaywrightTimeoutError:
                print("[PlaywrightScraper] Page body not found.")
                return None

            # Prefer main > article > body
            for selector in ["main", "article", "body"]:
                elements = page.locator(selector)
                if await elements.count() > 0:
                    text_content = await elements.first.inner_text()
                    break
            else:
                text_content = ""

            if text_content:
                text_content = "\n".join([line.strip() for line in text_content.splitlines() if line.strip()])

            print(f"[PlaywrightScraper] Successfully extracted content. Length: {len(text_content)} chars.")
            return text_content

    except PlaywrightTimeoutError as pte:
        print(f"[PlaywrightScraper] Timeout error for {url}: {pte}")
        return None
    except Exception as e:
        print(f"[PlaywrightScraper] General error for {url}: {e}")
        return None
    finally:
        if browser:
            print("[PlaywrightScraper] Closing browser.")
            await browser.close()


if __name__ == '__main__':
    async def main_test_playwright():
        test_url = "https://www.linkedin.com/in/nepalrabindra/"
        print(f"Attempting to scrape (Playwright): {test_url}")
        content = await scrape_with_playwright(test_url)
        if content:
            print(f"Successfully scraped content: \n{content}")
        else:
            print(f"Failed to scrape content from {test_url} using Playwright (may need 'playwright install' or URL is down).")
    asyncio.run(main_test_playwright())
