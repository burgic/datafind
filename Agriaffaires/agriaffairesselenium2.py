import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
import time
import random
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--window-size=1920,1080")
    firefox_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:92.0) Gecko/20100101 Firefox/92.0")
    
    service = FirefoxService('/usr/local/bin/geckodriver')
    
    driver = webdriver.Firefox(service=service, options=firefox_options)
    return driver

def fetch_listing_details(url, driver, max_retries=5):
    for attempt in range(max_retries):
        try:
            driver.get(url)
            # Wait for the page to load
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "listing-block")))
            
            # Scroll down the page to load any lazy-loaded content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)  # Increased wait time
            
            # Check if we've been redirected to a captcha or error page
            if "captcha" in driver.current_url or "error" in driver.current_url:
                logging.warning(f"Possible captcha or error page encountered on attempt {attempt + 1}")
                time.sleep(60)  # Wait longer before retrying
                continue
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract price
            price = 'N/A'
            price_tag = soup.find('div', class_='price txtcenter')
            if price_tag:
                price_value = price_tag.find('span', class_='js-priceToChange')
                currency_value = price_tag.find('span', class_='js-currencyToChange')
                if price_value and currency_value:
                    price = f"{price_value.text.strip()} {currency_value.text.strip()}"
            
            # Extract dealer information
            dealer = location = 'N/A'
            dealer_info = soup.find('div', class_='item-fluid item-center')
            if dealer_info:
                dealer_name_tag = dealer_info.find('p', class_='u-bold h3-like man')
                if dealer_name_tag:
                    dealer = dealer_name_tag.text.strip()
                location_tag = dealer_info.find('div', class_='u-bold')
                if location_tag:
                    location = location_tag.text.strip()

            # Extract phone numbers
            phone_numbers = []
            phone_list = soup.find('ul', id='js-dropdown-phone-2')
            if phone_list:
                for phone_tag in phone_list.find_all('a'):
                    phone_number = phone_tag.get('href', '').replace('tel://', '').strip()
                    phone_numbers.append(phone_number)
            
            # Extract table of specifications
            specs = {}
            table = soup.find('table', class_='table--specs')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) == 2:
                        key = cells[0].text.strip().replace(':', '')
                        value = cells[1].text.strip()
                        specs[key] = value

            return {
                'Price': price,
                'Dealer': dealer,
                'Location': location,
                'Phone Numbers': phone_numbers,
                'Specifications': specs
            }
        except TimeoutException:
            logging.warning(f"Timeout on attempt {attempt + 1} for URL: {url}")
        except (NoSuchElementException, WebDriverException) as e:
            logging.error(f"Error on attempt {attempt + 1} for URL {url}: {str(e)}")
        
        if attempt < max_retries - 1:
            wait_time = random.uniform(10, 30)
            logging.info(f"Waiting {wait_time:.2f} seconds before retrying...")
            time.sleep(wait_time)
    
    logging.error(f"Failed to scrape details after {max_retries} attempts: {url}")
    return None

def main():
    input_file = 'listings_2024-09-16.csv'  # Update this to your actual filename
    output_file = 'detailed_listings_selenium.csv'
    
    df = pd.read_csv(input_file)
    
    driver = setup_driver()
    detailed_listings = []

    for index, row in df.iterrows():
        url = row['URL']
        logging.info(f"Scraping details for: {url}")
        
        detailed_info = fetch_listing_details(url, driver)
        if detailed_info:
            detailed_listings.append({
                'Title': row['Title'],
                'URL': url,
                'Detailed Price': detailed_info.get('Price', 'N/A'),
                'Dealer': detailed_info.get('Dealer', 'N/A'),
                'Dealer Location': detailed_info.get('Location', 'N/A'),
                'Phone Numbers': ', '.join(detailed_info.get('Phone Numbers', [])),
                'Specifications': ', '.join([f"{k}: {v}" for k, v in detailed_info.get('Specifications', {}).items()])
            })
        else:
            logging.warning(f"Failed to scrape details for: {url}")
        
        wait_time = random.uniform(15, 30)
        logging.info(f"Waiting {wait_time:.2f} seconds before next request...")
        time.sleep(wait_time)
    
    driver.quit()

    # Save the detailed data to CSV
    pd.DataFrame(detailed_listings).to_csv(output_file, index=False)
    logging.info(f"Scraping completed. Results saved to {output_file}")

if __name__ == "__main__":
    main()