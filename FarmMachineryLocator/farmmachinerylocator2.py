import random
import requests
import time
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.124 Safari/537.36", 
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.124 Safari/537.36", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0", 
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:108.0) Gecko/20100101 Firefox/108.0", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54", 
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 12; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/15.0 Chrome/92.0.4515.166 Mobile Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    ]
    return random.choice(user_agents).strip()

def random_sleep(min_seconds, max_seconds):
    time.sleep(random.uniform(min_seconds, max_seconds))

def setup_driver():
    user_agent = get_random_user_agent()
    
    # Try Chrome
    try:
        options = ChromeOptions()
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"Chrome setup failed: {e}")
    
    # Try Firefox
    try:
        options = FirefoxOptions()
        options.add_argument(f"user-agent={user_agent}")
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference('useAutomationExtension', False)
        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=options)
    except Exception as e:
        print(f"Firefox setup failed: {e}")
    
    # Try Edge
    try:
        options = EdgeOptions()
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        service = EdgeService(EdgeChromiumDriverManager().install())
        return webdriver.Edge(service=service, options=options)
    except Exception as e:
        print(f"Edge setup failed: {e}")
    
    raise Exception("Failed to set up any supported browser.")

# Set up the driver
driver = setup_driver()

# URL of the first page to scrape
url = "https://www.farmmachinerylocator.co.uk/listings/search?Category=1100&Manufacturer=FENDT&Horsepower=100%2A"

# Function to scrape the data from the current page
def scrape_page():
    # Scroll the page slowly
    total_height = int(driver.execute_script("return document.body.scrollHeight"))
    for i in range(1, total_height, 3):
        driver.execute_script(f"window.scrollTo(0, {i});")
        random_sleep(0.05, 0.1)
    
    # Wait for the listings to load
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "list-listing-card-wrapper")]'))
    )
    
    listings = driver.find_elements(By.XPATH, '//div[contains(@class, "list-listing-card-wrapper")]')
    
    data = []
    for listing in listings:
        # Simulate human-like behavior by moving the mouse to the element
        ActionChains(driver).move_to_element(listing).perform()
        random_sleep(1, 3)
        
        try:
            name = listing.find_element(By.XPATH, './/h3[@class="listing-portion-title"]').text.strip()
            price = listing.find_element(By.XPATH, './/div[@class="price-contain"]//span[@class="price"]').text.strip()
            hours = listing.find_element(By.XPATH, './/div[@class="list-spec"]//span[@class="spec-value"]').text.strip()
            location = listing.find_element(By.XPATH, './/div[@class="machine-location"]').text.strip()
            phone = listing.find_element(By.XPATH, './/div[@class="dealer-data"]//a[@class="phone-link"]').text.strip()
            seller = listing.find_element(By.XPATH, './/div[@class="seller"]//a').text.strip()
            tractor_url = listing.find_element(By.XPATH, './/div[@class="listing-title"]//a').get_attribute('href')
            
            data.append({
                'Machine Name': name,
                'Price': price,
                'Hours': hours,
                'Location': location,
                'Phone Number': phone,
                'Seller': seller,
                'URL': tractor_url
            })
        except Exception as e:
            print(f"Error extracting data from listing: {e}")
    
    return data

# Create a CSV file to save the data
results_folder = './results'
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

url_part = url.split('/')[-1]
current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
csv_filename = f"{results_folder}/{current_time}_{url_part}.csv"

with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Machine Name', 'Price', 'Hours', 'Location', 'Phone Number', 'Seller', 'URL']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    page_number = 1
    while True:
        print(f"Navigating to page {page_number}...")
        if page_number == 1:
            driver.get(url)
        random_sleep(10, 15)
        
        print(f"Scraping page {page_number}...")
        data = scrape_page()
        
        if not data:
            print("No data found on this page. Ending scraping.")
            break
        
        for row in data:
            writer.writerow(row)
        
        try:
            next_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "pagination__next")]'))
            )
            if 'disabled' in next_button.get_attribute('class'):
                print("Reached the last page. Ending scraping.")
                break
            else:
                # Scroll to the next button
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                random_sleep(2, 4)
                next_button.click()
                page_number += 1
                random_sleep(10, 15)  # Longer wait between pages
        except Exception as e:
            print(f"Error navigating to the next page: {e}")
            break

driver.quit()
print(f"Data scraping completed. Check the file at {csv_filename} for the output.")