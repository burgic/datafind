import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime
import random
import time

def create_session():
    session = requests.Session()
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    ]
    session.headers.update({
        'User-Agent': random.choice(user_agents)
    })
    return session

def fetch_listings(main_url, session):
    listings = []
    max_retries = 3
    retry_delay = 10

    while max_retries > 0:
        print(f"Scraping page...")
        try:
            response = session.get(main_url)
            response.raise_for_status()
            
            print("Response status code:", response.status_code)
            soup = BeautifulSoup(response.text, 'html.parser')

            listing_blocks = soup.find_all('div', class_='listing-card-grid listing-data-selector')
            print(f"Found {len(listing_blocks)} listing blocks")

            for listing in listing_blocks:
                try:
                    # Extract title
                    title_tag = listing.find('h3', class_='listing-portion-title')
                    title = title_tag.text.strip() if title_tag else 'N/A'

                    # Extract link
                    link_tag = listing.find('a', class_='list-listing-title-link')
                    link = "https://www.farmmachinerylocator.co.uk" + link_tag['href'] if link_tag else 'N/A'

                    # Extract price
                    price_tag = listing.find('span', class_='price')
                    price = price_tag.text.strip() if price_tag else 'N/A'

                    # Extract hours
                    hours_tag = listing.find('span', class_='spec-value')
                    hours = hours_tag.text.strip() if hours_tag else 'N/A'

                    # Extract location
                    location_tag = listing.find('div', class_='machine-location')
                    location = location_tag.text.strip().replace('Location:', '').strip() if location_tag else 'N/A'

                    # Extract category
                    category_tag = listing.find('div', class_='listing-category')
                    category = category_tag.text.strip() if category_tag else 'N/A'

                    # Extract seller
                    seller_tag = listing.find('div', class_='seller')
                    seller = seller_tag.find('a').text.strip() if seller_tag else 'N/A'

                    listings.append({
                        'Title': title,
                        'Price': price,
                        'Hours': hours,
                        'Location': location,
                        'Category': category,
                        'Seller': seller,
                        'URL': link
                    })
                    print(f"Extracted listing: {title}")
                except Exception as e:
                    print(f"Error parsing a listing: {e}")

            print(f"Total listings extracted: {len(listings)}")
            break  # Successfully scraped, exit the loop

        except requests.exceptions.RequestException as e:
            print(f"Error: {e} - Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            max_retries -= 1

    return listings

def main():
    session = create_session()
    main_url = 'https://www.farmmachinerylocator.co.uk/listings/search?Category=1100&Manufacturer=FENDT&Horsepower=100%2A'
    listings = fetch_listings(main_url, session)

    if listings:
        today_date = datetime.now().strftime("%Y-%m-%d")
        filename = f'listings_{today_date}.csv'
        output_dir = './results'

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        filepath = os.path.join(output_dir, filename)
        df = pd.DataFrame(listings)
        df.to_csv(filepath, index=False)
        print(f"Data has been saved to {filepath}")
    else:
        print("No listings found.")

if __name__ == "__main__":
    main()