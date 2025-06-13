import asyncio
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def configure_stealth_options(headless: bool = True) -> ChromeOptions:
    options = ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    return options

async def scrape_with_selenium(url: str, headless: bool = True) -> Optional[str]:
    print(f">>>[SeleniumScraper] Attempting to scrape URL: {url}")
    driver = None
    try:
        options = configure_stealth_options(headless)
        driver = webdriver.Chrome(options=options)

        # Bypass basic automation detection
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })

        driver.get(url)

        cookie_buttons_selectors = [
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
            "//button[@id='onetrust-accept-btn-handler']"
        ]
        for selector in cookie_buttons_selectors:
            try:
                button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                button.click()
                await asyncio.sleep(2)
                break
            except:
                continue

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        main_content = soup.find("main") or soup.find("article") or soup.body

        return main_content.get_text(separator="\n", strip=True) if main_content else ""

    except Exception as e:
        print(f">>>[SeleniumScraper] Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    async def main_test_selenium():
        test_url = "https://en.wikipedia.org/wiki/Information_retrieval"
        test_url = "https://www.linkedin.com/in/mehret"
        print(f"Attempting to scrape (Selenium): {test_url}")
        content = await scrape_with_selenium(test_url)
        if content:
            print(f"Successfully scraped content:\n{content}")
        else:
            print(f"Failed to scrape content from {test_url} using Selenium (likely WebDriver setup issue in this environment).")
    asyncio.run(main_test_selenium())
