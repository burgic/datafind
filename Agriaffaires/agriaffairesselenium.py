import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_listing_details(url, driver):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "listing-block")))
        
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
    except Exception as e:
        print(f"Error: {e} while fetching details for {url}")
        return None

def main():
    # Load the CSV file with saved URLs
    input_file = 'listings_2024-09-16.csv'  # Update this to your actual filename
    output_file = 'detailed_listings_selenium.csv'
    
    df = pd.read_csv(input_file)
    
    driver = setup_driver()
    detailed_listings = []

    for index, row in df.iterrows():
        url = row['URL']
        print(f"Scraping details for: {url}")
        
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
        
        time.sleep(random.uniform(5, 10))  # Random delay between requests
    
    driver.quit()

    # Save the detailed data to CSV
    pd.DataFrame(detailed_listings).to_csv(output_file, index=False)
    print(f"Scraping completed successfully. Results saved to {output_file}")

if __name__ == "__main__":
    main()