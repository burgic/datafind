from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("ChromeDriver created successfully")
        return driver
    except Exception as e:
        logger.error(f"Error creating ChromeDriver: {e}")
        raise

def fetch_listings(main_url, driver):
    listings = []
    max_retries = 3
    retry_delay = 10

    while max_retries > 0:
        logger.info(f"Scraping page...")
        try:
            driver.get(main_url)
            logger.info(f"Navigated to URL: {main_url}")
            
            # Wait for the page to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info(f"Page title: {driver.title}")
            logger.info(f"Current URL: {driver.current_url}")
            
            # Get the page source and parse with BeautifulSoup
            page_source = driver.page_source
            logger.info(f"Page source length: {len(page_source)}")
            logger.info(f"First 500 characters of page source: {page_source[:500]}")
            
            soup = BeautifulSoup(page_source, 'html.parser')
            
            listing_blocks = soup.find_all('div', class_='listing-card-grid listing-data-selector')
            logger.info(f"Found {len(listing_blocks)} listing blocks")

            if len(listing_blocks) == 0:
                logger.info("Searching for any div with 'listing' in class name:")
                any_listings = soup.find_all('div', class_=lambda x: x and 'listing' in x)
                logger.info(f"Found {len(any_listings)} divs with 'listing' in class name")
                if any_listings:
                    logger.info(f"Classes found: {[div.get('class') for div in any_listings[:5]]}")

            for listing in listing_blocks:
                try:
                    # Extract listing details
                    title = listing.find('h3', class_='listing-portion-title').text.strip()
                    link = "https://www.farmmachinerylocator.co.uk" + listing.find('a', class_='list-listing-title-link')['href']
                    price = listing.find('span', class_='price').text.strip()
                    hours = listing.find('span', class_='spec-value').text.strip()
                    location = listing.find('div', class_='machine-location').text.strip().replace('Location:', '').strip()
                    category = listing.find('div', class_='listing-category').text.strip()
                    seller = listing.find('div', class_='seller').find('a').text.strip()

                    listings.append({
                        'Title': title,
                        'Price': price,
                        'Hours': hours,
                        'Location': location,
                        'Category': category,
                        'Seller': seller,
                        'URL': link
                    })
                    logger.info(f"Extracted listing: {title}")
                except Exception as e:
                    logger.error(f"Error parsing a listing: {e}")

            logger.info(f"Total listings extracted: {len(listings)}")
            break  # Successfully scraped, exit the loop

        except Exception as e:
            logger.error(f"Error: {e}")
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            max_retries -= 1

    return listings

def main():
    try:
        driver = create_driver()
        main_url = 'https://www.farmmachinerylocator.co.uk/listings/search?Category=1100&Manufacturer=FENDT&Horsepower=100%2A'
        listings = fetch_listings(main_url, driver)
        driver.quit()

        if listings:
            today_date = datetime.now().strftime("%Y-%m-%d")
            filename = f'listings_{today_date}.csv'
            output_dir = './results'

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            filepath = os.path.join(output_dir, filename)
            df = pd.DataFrame(listings)
            df.to_csv(filepath, index=False)
            logger.info(f"Data has been saved to {filepath}")
        else:
            logger.warning("No listings found.")
    except Exception as e:
        logger.error(f"An error occurred in main: {e}")

if __name__ == "__main__":
    main()