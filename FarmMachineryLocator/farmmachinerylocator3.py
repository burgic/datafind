import cloudscraper
from cloudscraper.exceptions import CloudflareChallengeError, CloudflareCaptchaError
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime
import time
import random
import requests

def create_session():
    session = cloudscraper.create_scraper()
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

            # Find all the listing blocks on the page
            listing_blocks = soup.find_all('div', class_='listing-card-grid listing-data-selector')
            print(f"Found {len(listing_blocks)} listing blocks")

            for listing in listing_blocks:
                try:
                    # Extract title and link
                    title_tag = listing.find('a', class_='listing-title-link')
                    title = title_tag.text.strip() if title_tag else 'N/A'
                    link = "https://www.farmmachinerylocator.co.uk" + title_tag['href'] if title_tag else 'N/A'

                    # Extract price
                    price_tag = listing.find('span', class_='price')
                    price = price_tag.text.strip() if price_tag else 'N/A'

                    # Extract hours
                    hours_tag = listing.find('span', class_='spec-value')
                    hours = hours_tag.text.strip() if hours_tag else 'N/A'

                    # Extract location
                    location_tag = listing.find('div', class_='machine-location')
                    location = location_tag.text.strip() if location_tag else 'N/A'

                    # Extract category (instead of seller, as seller is not visible in the provided HTML)
                    category_tag = listing.find('div', class_='listing-category')
                    category = category_tag.text.strip() if category_tag else 'N/A'

                    listings.append({
                        'Title': title,
                        'Price': price,
                        'Hours': hours,
                        'Location': location,
                        'Category': category,
                        'URL': link
                    })
                    print(f"Extracted listing: {title}")
                except Exception as e:
                    print(f"Error parsing a listing: {e}")

            print(f"Total listings extracted: {len(listings)}")
            break  # Successfully scraped, exit the loop

        except requests.exceptions.HTTPError as e:
            print(f"HTTPError: {e} - Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            max_retries -= 1

        except (CloudflareChallengeError, CloudflareCaptchaError) as e:
            print(f"Error fetching listings due to Cloudflare challenge: {e}")
            print("Response content:", response.text[:500])  # Print first 500 characters
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