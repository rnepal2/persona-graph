import asyncio
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup # For parsing page source if needed

# It's good practice to allow configuring webdriver path via env var or config
# For now, we'll assume chromedriver might be in PATH or use a service.
# More robust setup might involve webdriver-manager.

async def scrape_with_selenium(url: str, headless: bool = True) -> Optional[str]:
    """
    Scrapes a URL using Selenium to handle dynamic content.
    Attempts to handle basic cookie pop-ups.
    Returns the text content of the body, or None on error.
    """
    print(f"[SeleniumScraper] Attempting to scrape URL: {url}")
    driver = None  # Initialize driver to None for finally block

    try:
        chrome_options = ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox") # Common for Docker/CI environments
        chrome_options.add_argument("--disable-dev-shm-usage") # Common for Docker/CI
        chrome_options.add_argument("--disable-gpu")
        # Suppress console logs from Chrome/WebDriver
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])


        # Attempt to initialize WebDriver
        # This is the most environment-dependent part.
        # Using ChromeDriverManager is more robust but adds another dependency.
        # For now, assume chromedriver might be in PATH.
        print("[SeleniumScraper] Initializing WebDriver...")
        # driver = webdriver.Chrome(options=chrome_options) # This line often fails if chromedriver not in PATH
        # Let's use a more robust way with Service if available, or allow path specification
        # For simplicity in a sandboxed environment, we'll stick to the basic call
        # and expect it might fail, which is fine for testing the code structure.
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"[SeleniumScraper] WebDriver initialization failed: {e}")
            print("[SeleniumScraper] Common issues: ChromeDriver not in PATH or not executable.")
            print("[SeleniumScraper] Consider installing ChromeDriver or using webdriver-manager.")
            return None

        print(f"[SeleniumScraper] WebDriver initialized. Navigating to {url}...")
        driver.get(url)

        # Basic attempt to accept cookies (very heuristic)
        cookie_buttons_selectors = [
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow all')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'got it')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i understand')]",
            "//div[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept cookies')]",
             "//button[@id='onetrust-accept-btn-handler']" # Common ID
        ]
        for selector in cookie_buttons_selectors:
            try:
                # Wait a short time for button to be clickable
                button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"[SeleniumScraper] Found potential cookie button with selector: {selector}. Clicking...")
                button.click()
                print("[SeleniumScraper] Clicked cookie button.")
                await asyncio.sleep(2) # Give some time for overlay to disappear
                break # Stop after first successful click
            except:
                pass # Button not found or not clickable, try next selector

        # Wait for page body to be present, or a specific element if known
        print("[SeleniumScraper] Waiting for page content to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Extract text content - using BeautifulSoup on page_source can be effective
        # Or target specific main content areas if possible
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
        # Try to get main content, otherwise fall back to body
        main_content = soup.find("main") or soup.find("article") or soup.body
        if main_content:
            text_content = main_content.get_text(separator="\n", strip=True)
        else:
            text_content = "" # Should not happen if body is present

        print(f"[SeleniumScraper] Successfully extracted content. Length: {len(text_content)} chars.")
        return text_content

    except Exception as e:
        print(f"[SeleniumScraper] Error during Selenium scraping for {url}: {e}")
        return None
    finally:
        if driver:
            print("[SeleniumScraper] Quitting WebDriver.")
            driver.quit()

if __name__ == '__main__':
    async def main_test_selenium():
        # Test with a site known for dynamic content or cookie banners.
        # However, success depends heavily on the execution environment.
        # test_url = "https://www.example.com" # A simple site
        test_url = "http://web-scraping.dev/dynamic" # A site designed for testing, might not be live
        
        print(f"Attempting to scrape (Selenium): {test_url}")
        # In a restricted environment, webdriver setup might fail.
        # The function is designed to return None in that case.
        content = await scrape_with_selenium(test_url)
        if content:
            print(f"Successfully scraped content (first 500 chars):\n{content[:500]}")
        else:
            print(f"Failed to scrape content from {test_url} using Selenium (likely WebDriver setup issue in this environment).")
    
    asyncio.run(main_test_selenium())
