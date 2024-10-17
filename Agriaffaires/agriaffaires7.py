
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

def fetch_listing_urls(main_url, session):
    listings = []
    current_page = 1
    max_retries = 3
    retry_delay = 10
    today_date = datetime.now().strftime("%Y-%m-%d")
    filename = f'listings_{today_date}.csv'

    while True:
        print(f"Scraping page {current_page} for URLs...")
        try:
            response = session.get(main_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get the total number of pages (only on the first page)
            if current_page == 1:
                total_pages = get_total_pages(soup)
                print(f"Total pages to scrape: {total_pages}")

            # Find all the listing blocks on the page
            for i, listing in enumerate(soup.find_all('div', class_='listing-block')):
                print(f"Inspecting listing {i+1}:")
                print(listing.prettify())  # Print the raw HTML structure of the listing block for inspection
                
                # Extract title and link
                link_tag = listing.find('a', class_='listing-block__link')
                if link_tag:
                    title = link_tag.find('span', class_='listing-block__title').text.strip() if link_tag else 'N/A'
                    link = "https://www.agriaffaires.co.uk" + link_tag.get('href', 'N/A')
                    print(f"Found listing: {title}, URL: {link}")
                else:
                    print("No valid link found in this listing")
                    title = "N/A"
                    link = "N/A"

                if link == 'N/A':
                    print(f"Skipping listing with no valid URL: {title}")
                    continue  # Skip listings without a valid URL

                # Add basic listing data
                listings.append({
                    'Title': title,
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


def fetch_listing_details(url, session):
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
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
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError: {e} while fetching details for {url}")
        return None
    except Exception as e:
        print(f"Error: {e} while fetching details for {url}")
        return None

def main():
    session = create_session()
    main_url = 'https://www.agriaffaires.co.uk/used/1/farm-tractor.html'

    # Step 1: Fetch basic listing data
    listings = fetch_listing_urls(main_url, session)

    # Step 2: Fetch detailed data for each listing
    detailed_listings = []
    for listing in listings:
        detailed_info = fetch_listing_details(listing['URL'], session)
        if detailed_info:
            # Combine the basic and detailed information
            detailed_listings.append({
                **listing,  # Include all the basic data
                'Detailed Price': detailed_info.get('Price', 'N/A'),
                'Dealer': detailed_info.get('Dealer', 'N/A'),
                'Dealer Location': detailed_info.get('Location', 'N/A'),
                'Phone Numbers': detailed_info.get('Phone Numbers', []),
                'Specifications': detailed_info.get('Specifications', {})
            })

    # Save the detailed data to CSV
    today_date = datetime.now().strftime("%Y-%m-%d")
    filename = f'detailed_listings_{today_date}.csv'
    save_data_to_csv(detailed_listings, filename)

    if detailed_listings:
        print("Scraping completed successfully.")
    else:
        print("No listings found.")

if __name__ == "__main__":
    main()
