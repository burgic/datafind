from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import csv
import os
from datetime import datetime
import random

# Set up Chrome browser
options = Options()
# options.headless = True  # Uncomment to run in headless mode
options.add_argument("user-agent=" + random.choice([
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:68.0) Gecko/20100101 Firefox/68.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
]))

driver = webdriver.Chrome(options=options)

# Function to scrape a single page
def scrape_page():
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
with open(csv_filename, 'w', newline='') as csvfile:
    fieldnames = ['Tractor Name', 'Hours', 'Location', 'Price', 'URL']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

# Loop through pagination
while True:
    scrape_page()

    try:
        # Check if there's a "Next" button for pagination
        next_button = driver.find_element(By.CSS_SELECTOR, '.pagination-next a')
        time.sleep(random.uniform(2, 5))  # Random delay
        next_button.click()
        time.sleep(random.uniform(3, 7))  # Wait for the next page to load
    except:
        break  # No more pages, exit the loop

driver.quit()
print(f"Data scraping completed. Check the file at {csv_filename} for the output.")
