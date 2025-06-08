import asyncio
import subprocess
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

async def ensure_playwright_install():
    """Ensure Playwright browsers are installed"""
    try:
        subprocess.run(['playwright', 'install'], check=True)
        return True
    except Exception as e:
        print(f"Failed to install Playwright browsers: {e}")
        return False

async def scrape_with_playwright(url: str, headless: bool = True) -> Optional[str]:
    """
    Scrapes a URL using Playwright to handle dynamic content.
    Attempts to handle cookie pop-ups and extracts content intelligently.
    Returns the text content of the body, or None on error.
    """
    print(f"[PlaywrightScraper] Attempting to scrape URL: {url}")
    browser = None

    try:
        async with async_playwright() as p:
            print("[PlaywrightScraper] Launching browser...")
            
            # Try browsers in order
            browser_types = [
                ("chromium", p.chromium),
                ("firefox", p.firefox)
            ]
            
            for browser_name, browser_type in browser_types:
                try:
                    launch_args = {
                        "headless": headless,
                    }
                    
                    if browser_name == "chromium":
                        launch_args["args"] = ["--no-sandbox", "--disable-blink-features=AutomationControlled"]
                    
                    browser = await browser_type.launch(**launch_args)
                    print(f"[PlaywrightScraper] Successfully launched {browser_name}")
                    break
                except Exception as e:
                    print(f"[PlaywrightScraper] Failed to launch {browser_name}: {e}")
                    continue
            
            if browser is None:
                print("[PlaywrightScraper] Attempting to install browsers...")
                if await ensure_playwright_install():
                    browser = await p.chromium.launch(
                        headless=headless,
                        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
                    )
                else:
                    raise Exception("Failed to install and launch any browser")

            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            print(f"[PlaywrightScraper] Navigating to {url}...")
            
            # Enhanced navigation with retry logic
            for wait_until in ["networkidle", "load", "domcontentloaded"]:
                try:
                    response = await page.goto(
                        url, 
                        wait_until=wait_until, 
                        timeout=30000 if wait_until == "networkidle" else 15000
                    )
                    if response and response.ok:
                        break
                    elif response and response.status >= 400:
                        print(f"[PlaywrightScraper] HTTP {response.status} error loading {url}")
                        return None
                except PlaywrightTimeoutError:
                    print(f"[PlaywrightScraper] Timeout with {wait_until}, trying next strategy...")
                    continue
                except Exception as e:
                    print(f"[PlaywrightScraper] Navigation error: {e}")
                    return None

            # Handle cookie pop-ups and banners
            cookie_buttons_selectors = [
                "button:has-text('accept all')", 
                "button:has-text('allow all')",
                "button:has-text('agree')", 
                "button:has-text('got it')",
                "button:has-text('i understand')",
                "div[role='button']:has-text('accept')",
                "#onetrust-accept-btn-handler",
                "[aria-label*='accept cookies' i]",
                "[data-testid*='cookie-accept']"
            ]
            
            for selector in cookie_buttons_selectors:
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=1000):
                        await button.click(timeout=3000)
                        print(f"[PlaywrightScraper] Clicked cookie button: {selector}")
                        await page.wait_for_timeout(2000)
                        break
                except Exception:
                    continue

            # Intelligent content extraction
            content = ""
            try:
                # Wait for content to load
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass

            # Try to get main content first
            for main_selector in ["main", "article", "[role='main']", "#main-content", ".main-content"]:
                try:
                    main_content = await page.locator(main_selector).first.inner_text()
                    if main_content and len(main_content) > 100:
                        content = main_content
                        break
                except Exception:
                    continue

            # Fallback to body if no main content found
            if not content:
                try:
                    # Remove common noise elements first
                    await page.evaluate("""() => {
                        const selectors = [
                            'header', 'footer', 'nav', '[role="navigation"]',
                            'style', 'script', 'noscript', 'iframe',
                            '.cookie-banner', '#cookie-banner',
                            '.advertisement', '.ad-container',
                            '.sidebar', '.comments'
                        ];
                        selectors.forEach(selector => {
                            document.querySelectorAll(selector).forEach(el => el.remove());
                        });
                    }""")
                    content = await page.locator("body").inner_text()
                except Exception as e:
                    print(f"[PlaywrightScraper] Error extracting content: {e}")
                    return None

            return content.strip() if content else None

    except Exception as e:
        print(f"[PlaywrightScraper] Scraping failed: {e}")
        return None
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass

if __name__ == '__main__':
    async def main_test_playwright():
        test_url = "https://www.linkedin.com/in/nepalrabindra/"
        print(f"Attempting to scrape (Playwright): {test_url}")
        content = await scrape_with_playwright(test_url)
        if content:
            print(f"Successfully scraped content: \n{content[:500]}...")  # Print first 500 chars
        else:
            print(f"Failed to scrape content from {test_url} using Playwright (may need 'playwright install' or URL is down).")
    
    asyncio.run(main_test_playwright())
