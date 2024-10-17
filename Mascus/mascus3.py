from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
import os
from datetime import datetime

# Set up Firefox browser (non-headless for debugging)
options = Options()
options.headless = False  # Set to True for production
driver = webdriver.Firefox(options=options)

# Increase the page load timeout
driver.set_page_load_timeout(60)

# Base URL of the page to scrape
base_url = "https://www.mascus.co.uk/agriculture/tractors/case_ih"
driver.get(base_url)

results_folder = './results'
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

url_part = base_url.split('/')[-1]

current_time = datetime.now().strftime('%Y%m%d_%H%M%S')

csv_filename = f"{results_folder}/{current_time}_{url_part}.csv"


def wait_for_element(driver, by, value, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )

def enhanced_scroll():
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_down_increment = 4000  # Scroll down by 4000 pixels at a time
    scroll_up_increment = 1000  # Scroll up by 1000 pixels at a time
    max_no_change = 3  # Maximum number of iterations with no content change
    no_change_count = 0

    while no_change_count < max_no_change:
        # Scroll down incrementally
        driver.execute_script(f"window.scrollBy(0, {scroll_down_increment});")
        time.sleep(2)  # Wait for content to load

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height > last_height:
            # New content has been loaded, reset the no change counter
            last_height = new_height
            no_change_count = 0
        else:
            # No new content loaded, start scrolling back up incrementally
            for _ in range(10):
                driver.execute_script(f"window.scrollBy(0, -{scroll_up_increment});")
                time.sleep(1)
                new_height = driver.execute_script("return document.body.scrollHeight")

                if new_height > last_height:
                    # New content has been loaded, break out of the scroll back loop
                    last_height = new_height
                    no_change_count = 0
                    break
            else:
                # Increment no change counter if still no new content is loaded
                no_change_count += 1

def extract_listing_data(listing):
    try:
        name = listing.find_element(By.CSS_SELECTOR, '.SearchResult_brandmodel__04K2L').text.strip()
        year_and_location = listing.find_element(By.CSS_SELECTOR, '.typography__BodyText2-sc-1tyz4zr-2').text.strip()
        parts = year_and_location.split(' • ')
        year = parts[1] if len(parts) > 1 else 'N/A'
        hours = parts[2] if len(parts) > 2 else 'N/A'
        company = listing.find_element(By.CSS_SELECTOR, '.SearchResult_companyName__ZDruC').text.strip()
        tractor_url = listing.find_element(By.CSS_SELECTOR, '.SearchResult_assetHeaderUrl__EMde6').get_attribute('href')
        
        try:
            company_url_element = listing.find_element(By.CSS_SELECTOR, '.SearchResult_companyWrapper__W5gTQ a')
            company_url = f"https://www.mascus.co.uk{company_url_element.get_attribute('href')}"
        except NoSuchElementException:
            company_url = 'N/A'

        return {
            'Tractor Name': name,
            'Year': year,
            'Hours': hours,
            'Company': company,
            'Company URL': company_url,
            'URL': tractor_url
        }
    except Exception as e:
        print(f"Error extracting listing data: {str(e)}")
        return None

with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Tractor Name', 'Year', 'Hours', 'Company', 'Company URL', 'URL']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    total_processed = 0
    page_number = 1

    while True:
        print(f"Processing page {page_number}...")

        # Perform enhanced scroll to load all listings on the current page
        enhanced_scroll()

        # Extract data from current page
        listings = driver.find_elements(By.CSS_SELECTOR, '.SearchResult_searchResultItemWrapper__VVVnZ')
        print(f"Found {len(listings)} listings on page {page_number}")
        
        for index, listing in enumerate(listings, 1):
            data = extract_listing_data(listing)
            if data:
                writer.writerow(data)
                total_processed += 1
            
            if index % 10 == 0:
                print(f"Processed {index} out of {len(listings)} listings on page {page_number}")

        print(f"Completed processing page {page_number}")

        # Navigate to next page
        try:
            next_button = wait_for_element(driver, By.CSS_SELECTOR, 'a[aria-label="Next"]')
            if 'disabled' in next_button.get_attribute('class'):
                print("Reached last page")
                break
            
            next_button.click()
            page_number += 1
            time.sleep(10)  # Wait for the next page to load
            # Wait for the first listing on the new page to ensure it's loaded
            wait_for_element(driver, By.CSS_SELECTOR, '.SearchResult_searchResultItemWrapper__VVVnZ')
        except (NoSuchElementException, TimeoutException):
            print("No more pages found or timeout occurred")
            break

driver.quit()
print(f"Data scraping completed. Total listings processed: {total_processed}")
print(f"Check the file at {csv_filename} for the output.")
