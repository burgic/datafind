from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import time
import csv
import os
from datetime import datetime

# Set up headless Firefox browser
options = Options()
options.headless = True
driver = webdriver.Firefox(options=options)

# URL of the page to scrape
url = "https://www.mascus.co.uk/agriculture/tractors/case_ih"
driver.get(url)

# Infinite scroll handling by scrolling incrementally
scroll_pause_time = 2
scroll_increment = 1000  # Scroll down by 1000 pixels at a time
max_scroll_attempts = 5  # Maximum attempts to detect new content before stopping

last_position = driver.execute_script("return window.pageYOffset;")
scroll_attempts = 0

while scroll_attempts < max_scroll_attempts:
    driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
    time.sleep(scroll_pause_time)
    
    new_position = driver.execute_script("return window.pageYOffset;")
    listings = driver.find_elements(By.CSS_SELECTOR, '.SearchResult_searchResultItemWrapper__VVVnZ')
    
    # Check if new items are loaded
    if new_position == last_position:
        scroll_attempts += 1
    else:
        scroll_attempts = 0  # Reset if new content is found
        last_position = new_position

results_folder = './results'
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

url_part = url.split('/')[-1]

current_time = datetime.now().strftime('%Y%m%d_%H%M%S')

csv_filename = f"{results_folder}/{current_time}_{url_part}.csv"

# Create a CSV file to save the data
with open(csv_filename, 'w', newline='') as csvfile:
    fieldnames = ['Tractor Name', 'Year', 'Hours', 'Company', 'Company URL', 'URL']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Iterate through all loaded tractor listings
    for listing in listings:
        # Extract tractor name
        name = listing.find_element(By.CSS_SELECTOR, '.SearchResult_brandmodel__04K2L').text.strip()
        
        # Extract year, hours, and company if available
        year_and_location = listing.find_element(By.CSS_SELECTOR, '.typography__BodyText2-sc-1tyz4zr-2').text.strip()
        parts = year_and_location.split(' • ')
        year = parts[1] if len(parts) > 1 else 'N/A'
        hours = parts[2] if len(parts) > 2 else 'N/A'  # Extract hours

        company = listing.find_element(By.CSS_SELECTOR, '.SearchResult_companyName__ZDruC').text.strip()

        # Extract URL of the listing
        tractor_url = listing.find_element(By.CSS_SELECTOR, '.SearchResult_assetHeaderUrl__EMde6').get_attribute('href')

        # Check if the company URL element exists and extract it
        try:
            company_url_element = listing.find_element(By.CSS_SELECTOR, '.SearchResult_companyWrapper__W5gTQ a')
            company_url = f"https://www.mascus.co.uk{company_url_element.get_attribute('href')}"
        except:
            company_url = 'N/A'  # If the company URL is not found, set as N/A

        # Write the extracted data to the CSV file
        writer.writerow({
            'Tractor Name': name,
            'Year': year,
            'Hours': hours,  # Save hours in the CSV
            'Company': company,
            'Company URL': company_url,
            'URL': tractor_url
        })

driver.quit()
print(f"Data scraping completed. Check the file at {csv_filename} for the output.")
