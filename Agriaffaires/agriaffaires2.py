from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import os
from datetime import datetime
import random

# Set up Chrome browser
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-extensions")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("user-agent=" + random.choice([
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]))

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Function to scrape a single page
def scrape_page():
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.listing-block--classified')))
    listings = driver.find_elements(By.CSS_SELECTOR, '.listing-block--classified')

    for listing in listings:
        # Extract tractor name
        name = listing.find_element(By.CSS_SELECTOR, '.listing-block__title span').text.strip()

        # Extract hours
        try:
            hours = listing.find_element(By.CSS_SELECTOR, '.listing-block__description span').text.strip()
        except:
            hours = 'N/A'

        # Extract location
        location = listing.find_element(By.CSS_SELECTOR, '.listing-block__localisation').text.strip()

        # Extract price
        try:
            price = listing.find_element(By.CSS_SELECTOR, '.listing-block__price .js-priceToChange').text.strip()
        except:
            price = 'N/A'

        # Extract URL of the listing
        tractor_url = listing.find_element(By.CSS_SELECTOR, '.listing-block__link').get_attribute('href')

        # Write the extracted data to the CSV file
        writer.writerow({
            'Tractor Name': name,
            'Hours': hours,
            'Location': location,
            'Price': price,
            'URL': tractor_url
        })

# URL of the first page to scrape
base_url = "https://www.agriaffaires.co.uk/used/1/farm-tractor.html"
driver.get(base_url)

results_folder = './results'
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

url_part = "agriaffaires_farm_tractor"
current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
csv_filename = f"{results_folder}/{current_time}_{url_part}.csv"

# Create a CSV file to save the data
with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Tractor Name', 'Hours', 'Location', 'Price', 'URL']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Loop through pagination
    page_number = 1
    while True:
        print(f"Scraping page {page_number}")
        scrape_page()

        try:
            # Check if there's a "Next" button for pagination
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.pagination-next a'))
            )
            time.sleep(random.uniform(5, 10))  # Longer random delay
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(random.uniform(7, 12))  # Wait longer for the next page to load
            page_number += 1
        except:
            break  # No more pages, exit the loop

driver.quit()
print(f"Data scraping completed. Check the file at {csv_filename} for the output.")