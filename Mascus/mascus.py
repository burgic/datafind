from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

# Set up headless Firefox browser
options = Options()
options.headless = True
driver = webdriver.Firefox(options=options)

# URL of the page to scrape
url = "https://www.mascus.co.uk/agriculture/tractors/new_holland"
driver.get(url)

# Wait for the page to fully load
time.sleep(5)  # Adjust the sleep time as necessary

# Wait until the search items are loaded
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.SearchResult_searchResultItemWrapper__VVVnZ'))
    )

    # Create a CSV file to save the data
    with open('tractors.csv', 'w', newline='') as csvfile:
        fieldnames = ['Tractor Name', 'Year', 'Hours', 'Company', 'URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Find all tractor listings on the page
        listings = driver.find_elements(By.CSS_SELECTOR, '.SearchResult_searchResultItemWrapper__VVVnZ')

        for listing in listings:
            # Extract tractor name
            name = listing.find_element(By.CSS_SELECTOR, '.SearchResult_brandmodel__04K2L').text.strip()
            
            # Extract year, hours, and company if available
            year_and_location = listing.find_element(By.CSS_SELECTOR, '.typography__BodyText2-sc-1tyz4zr-2').text.strip()
            year = year_and_location.split(' • ')[1] if ' • ' in year_and_location else 'N/A'

            company = listing.find_element(By.CSS_SELECTOR, '.SearchResult_companyLink__H0rdK').text.strip()

            # Extract URL of the listing
            tractor_url = listing.find_element(By.CSS_SELECTOR, '.SearchResult_assetHeaderUrl__EMde6').get_attribute('href')

            # Write the extracted data to the CSV file
            writer.writerow({
                'Tractor Name': name,
                'Year': year,
                'Hours': 'N/A',  # If hours are not present, keep as N/A
                'Company': company,
                'URL': tractor_url
            })

    print("Data scraping completed. Check the tractors.csv file for the output.")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.quit()