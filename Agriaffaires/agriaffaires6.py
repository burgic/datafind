import cloudscraper
import requests
from cloudscraper.exceptions import CloudflareChallengeError, CloudflareCaptchaError
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime
import time
import random

def create_session():
    # Use cloudscraper to handle websites with Cloudflare
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

def get_total_pages(soup):
    # Find the pagination element and extract the total number of pages
    pagination_text = soup.find('li', class_='pagination--simple').text.strip()
    total_pages = int(pagination_text.split('/')[-1].strip())
    return total_pages

def save_data_to_csv(listings, filename):
    output_dir = './results'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filepath = os.path.join(output_dir, filename)
    df = pd.DataFrame(listings)
    df.to_csv(filepath, index=False)
    print(f"Data has been saved to {filepath}")

def fetch_listings(main_url, session):
    listings = []
    current_page = 1
    max_retries = 3
    retry_delay = 10
    today_date = datetime.now().strftime("%Y-%m-%d")
    filename = f'listings_{today_date}.csv'

    while True:
        print(f"Scraping page {current_page}...")
        try:
            response = session.get(main_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get the total number of pages (only on the first page)
            if current_page == 1:
                total_pages = get_total_pages(soup)
                print(f"Total pages to scrape: {total_pages}")

            # Find all the listing blocks on the page
            for listing in soup.find_all('div', class_='listing-block'):
                # Extract title and link
                link_tag = listing.find('a', class_='listing-block__link')
                title = link_tag.find('span', class_='listing-block__title').text.strip() if link_tag else 'N/A'
                link = "https://www.agriaffaires.co.uk" + link_tag['href'] if link_tag else 'N/A'
                
                # Extract year, hours, and horsepower
                description_tag = listing.find('div', class_='listing-block__description')
                year = hours = horsepower = 'N/A'
                if description_tag:
                    desc_spans = description_tag.find_all('span')
                    if len(desc_spans) > 1:
                        year = desc_spans[1].text.strip() if desc_spans[1] else 'N/A'
                    if len(desc_spans) > 3:
                        hours = desc_spans[3].text.strip() if desc_spans[3] else 'N/A'
                    if len(desc_spans) > 5:
                        horsepower = desc_spans[5].text.strip() if desc_spans[5] else 'N/A'

                # Extract location
                location_tag = listing.find('div', class_='listing-block__localisation')
                location = location_tag.text.strip().replace('\n', ', ').replace(' ,', ',') if location_tag else 'N/A'

                # Extract price
                price_tag = listing.find('div', class_='listing-block__price')
                price = currency = 'N/A'
                if price_tag:
                    price_value = price_tag.find('span', class_='js-priceToChange')
                    price = price_value.text.strip() if price_value else 'N/A'
                    currency_value = price_tag.find('span', class_='js-currencyToChange')
                    currency = currency_value.text.strip() if currency_value else 'N/A'
                    price = f"{price} {currency}"
                
                # Create a dictionary of the extracted data
                listings.append({
                    'Title': title,
                    'Year': year,
                    'Hours': hours,
                    'Horsepower': horsepower,
                    'Location': location,
                    'Price': price,
                    'URL': link
                })

            # Save data after each page
            save_data_to_csv(listings, filename)

            # Check if we've reached the last page
            if current_page >= total_pages:
                print("Reached the last page.")
                break

            # Find the next page link
            current_page += 1
            next_page_url = f"https://www.agriaffaires.co.uk/used/{current_page}/farm-tractor.html"
            main_url = next_page_url  # Update main_url to the next page
            time.sleep(random.uniform(5, 10))  # Randomize delay between 5 to 10 seconds to reduce blocking

        except requests.exceptions.HTTPError as e:
            print(f"HTTPError: {e} - Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            max_retries -= 1
            if max_retries == 0:
                print("Max retries reached. Saving data and stopping scraper.")
                save_data_to_csv(listings, filename)
                break

        except (CloudflareChallengeError, CloudflareCaptchaError) as e:
            print(f"Error fetching listings due to Cloudflare challenge: {e}")
            save_data_to_csv(listings, filename)
            break

    return listings

def main():
    session = create_session()
    main_url = 'https://www.agriaffaires.co.uk/used/1/farm-tractor.html'
    listings = fetch_listings(main_url, session)

    if listings:
        print("Scraping completed successfully.")
    else:
        print("No listings found.")

if __name__ == "__main__":
    main()
