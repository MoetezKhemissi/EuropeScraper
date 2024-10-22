import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.options import Options

# ====================== Configuration ======================

# Path to your ChromeDriver executable
CHROMEDRIVER_PATH = 'path_to_chromedriver'  # Replace with your actual path, e.g., 'C:/drivers/chromedriver.exe'

# URL to scrape
TARGET_URL = "https://www.europarl.europa.eu/RegistreWeb/search/simple.htm?endDate=1725206399999&types=PCREP&sortAndOrder=DATE_DOCU_DESC"

# Directory to save PDFs
DOWNLOAD_DIR = 'pdfs'

# Maximum time to wait for elements (in seconds)
MAX_WAIT_TIME = 15

# Delay between actions to allow dynamic content to load
ACTION_DELAY = 1  # in seconds

# Maximum number of "Load more" clicks to prevent infinite loops
MAX_LOAD_MORE_CLICKS = 1500

# ============================================================

def setup_driver():
    """
    Set up the Selenium WebDriver with necessary options.
    """
    chrome_options = Options()
    # Uncomment the following line to run Chrome in headless mode
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")  # Linux specific
    chrome_options.add_argument("--window-size=1920,1080")
    

    driver = webdriver.Chrome( options=chrome_options)
    return driver

def click_load_more(driver):
    """
    Continuously click the "Load more" button until it's no longer present or maximum clicks reached.
    """
    load_more_clicks = 0
    while load_more_clicks < MAX_LOAD_MORE_CLICKS:
        try:
            # Wait until the "Load more" button is present and visible
            load_more_button = WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'btn') and normalize-space(text())='Load more']")
                )
            )
            print(f"'Load more' button found. Attempting to click (Click {load_more_clicks + 1}/{MAX_LOAD_MORE_CLICKS})...")
            
            # Scroll the "Load more" button into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
            time.sleep(ACTION_DELAY)  # Small delay to ensure scrolling has completed
            
            try:
                # Attempt to click using Selenium's native click
                load_more_button.click()
                print("Clicked 'Load more' button using Selenium's click.")
            except ElementClickInterceptedException:
                # If the element is obscured, use JavaScript to click
                print("Selenium click intercepted. Attempting to click using JavaScript.")
                driver.execute_script("arguments[0].click();", load_more_button)
                print("Clicked 'Load more' button using JavaScript.")
            
            load_more_clicks += 1
            # Wait for new content to load
            time.sleep(2)  # Adjust if necessary
        except TimeoutException:
            print("No more 'Load more' button found or timeout reached.")
            break
        except NoSuchElementException:
            print("No 'Load more' button found on the page.")
            break
    if load_more_clicks >= MAX_LOAD_MORE_CLICKS:
        print(f"Reached the maximum number of 'Load more' clicks ({MAX_LOAD_MORE_CLICKS}).")
    else:
        print(f"Total 'Load more' clicks performed: {load_more_clicks}")

def download_pdf(pdf_url, download_path):
    """
    Download the PDF from the given URL and save it to the specified path.
    """
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()  # Check for HTTP errors
        with open(download_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {download_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {pdf_url}: {e}")

def main():
    # Create download directory if it doesn't exist
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"Created directory: {DOWNLOAD_DIR}")

    # Initialize the WebDriver
    driver = setup_driver()
    driver.get(TARGET_URL)
    print(f"Navigated to {TARGET_URL}")

    # Load all items by clicking "Load more"
    click_load_more(driver)

    # Wait for all items to be present
    try:
        WebDriverWait(driver, MAX_WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.erpl_search-results-item'))
        )
        print("All search result items are loaded.")
    except TimeoutException:
        print("Timeout while waiting for search result items to load.")

    # Find all search result items
    search_items = driver.find_elements(By.CSS_SELECTOR, 'div.erpl_search-results-item')
    print(f"Found {len(search_items)} search result items.")

    for index, item in enumerate(search_items, start=1):
        try:
            # Locate the <h3> element within the item
            h3_element = item.find_element(By.CSS_SELECTOR, 'h3.erpl_search-results-item-title')

            # Scroll into view to ensure the element is visible
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", h3_element)
            time.sleep(ACTION_DELAY)  # Small delay to ensure scrolling has completed

            # Wait until the <h3> is clickable
            WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.element_to_be_clickable(
                    (By.XPATH, ".//h3[contains(@class, 'erpl_search-results-item-title')]")
                )
            )

            # Click the <h3> to expand the details using JavaScript to avoid interception
            try:
                driver.execute_script("arguments[0].click();", h3_element)
                print(f"Clicked on item {index}: {h3_element.text.strip()}")
            except Exception as e:
                print(f"Failed to click on <h3> for item {index}: {e}")
                continue

            # Wait until the PDF link is present within the expanded details
            try:
                pdf_link_element = WebDriverWait(item, MAX_WAIT_TIME).until(
                    EC.presence_of_element_located(
                        (By.XPATH, ".//a[contains(@class, 't-item') and contains(@href, '.pdf')]")
                    )
                )
                pdf_url = pdf_link_element.get_attribute('href')
                if pdf_url:
                    # Extract the PDF file name
                    pdf_name = pdf_url.split('/')[-1]
                    download_path = os.path.join(DOWNLOAD_DIR, pdf_name)

                    # Check if the PDF already exists to avoid duplicates
                    if not os.path.exists(download_path):
                        download_pdf(pdf_url, download_path)
                    else:
                        print(f"Already downloaded: {download_path}")
                else:
                    print(f"No PDF URL found for item {index}.")
            except TimeoutException:
                print(f"PDF link not found for item {index}: {h3_element.text.strip()}")

            # Optionally, collapse the details by clicking again
            # driver.execute_script("arguments[0].click();", h3_element)
            # time.sleep(ACTION_DELAY)

        except NoSuchElementException:
            print(f"No <h3> element found for item {index}. Skipping.")
        except ElementClickInterceptedException:
            print(f"Could not click on <h3> for item {index}. It might be obscured.")
        except StaleElementReferenceException:
            print(f"Stale element reference for item {index}. It might have been updated. Skipping.")
        except Exception as e:
            print(f"An unexpected error occurred for item {index}: {e}")

    # Close the WebDriver
    driver.quit()
    print("Scraping completed.")

if __name__ == "__main__":
    main()
