
import cloudscraper
import requests
from cloudscraper.exceptions import CloudflareChallengeError, CloudflareCaptchaError
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime
import time
import random

def get_random_user_agent():
    # Use cloudscraper to handle websites with Cloudflare
    session = cloudscraper.create_scraper()
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:85.0) Gecko/20100101 Firefox/85.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/602.4.8 (KHTML, like Gecko) Version/10.1.2 Safari/602.4.8',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.100.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.49',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36 Edg/89.0.774.50',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36 Edg/88.0.705.50',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66',
        'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Googlebot/2.1 (+http://www.googlebot.com/bot.html)',
        'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',

 ]
    return random.choice(user_agents)

def get_headers():
    return {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
session_pool = []

def create_session():
       session = cloudscraper.create_scraper()
       session.headers.update(get_headers())
       return session

def create_session_pool(pool_size = 3):
    return [create_session() for _ in range(pool_size)]

def get_random_session():
    return random.choice(session_pool)


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
    page_limit = 5

    while True:
        if current_page > page_limit:
            print("Reached the testing limit of 5 pages")
            break 

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

            # Save the basic data after each page
            save_data_to_csv(listings, filename)

            # Check if we've reached the last page
            if current_page >= total_pages:
                print("Reached the last page.")
                break

            # Find the next page link
            current_page += 1
            next_page_url = f"https://www.agriaffaires.co.uk/used/farm-tractor/{current_page}/4044/massey-ferguson.html"
            main_url = next_page_url  # Update main_url to the next page
            time.sleep(random.uniform(10, 20))  # Randomize delay between 5 to 10 seconds to reduce blocking

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
    global session_pool
    session = create_session()
    session_pool = create_session_pool()
    main_url = 'https://www.agriaffaires.co.uk/used/farm-tractor/1/4044/massey-ferguson.html'

    # Step 1: Fetch basic listing data
    listings = fetch_listing_urls(main_url, session)

    # Step 2: Fetch detailed data for each listing
    detailed_listings = []
    for listing in listings:
        session = get_random_session()
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
        time.sleep(random.uniform(5, 10))  # Randomize delay between 5 to 10 seconds to reduce blocking

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