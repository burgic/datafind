import cloudscraper
import requests
from cloudscraper.exceptions import CloudflareChallengeError, CloudflareCaptchaError
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime
import time
import random
import urllib3
from collections import defaultdict

urllib3.disable_warnings()

class ProxyManager:
    def __init__(self, proxies):
        self.proxies = proxies
        self.failed_counts = defaultdict(int)
        self.backoff_times = defaultdict(float)

    def get_proxy(self):
        current_time = time.time()
        available_proxies = [p for p in self.proxies if current_time > self.backoff_times[p]]
        if not available_proxies:
            time.sleep(5)  # Wait if all proxies are on backoff
            return self.get_proxy()
        return min(available_proxies, key=lambda p: self.failed_counts[p])

    def mark_failed(self, proxy):
        self.failed_counts[proxy] += 1
        backoff_time = min(60 * 2 ** self.failed_counts[proxy], 3600)  # Max 1 hour backoff
        self.backoff_times[proxy] = time.time() + backoff_time

    def mark_success(self, proxy):
        self.failed_counts[proxy] = max(0, self.failed_counts[proxy] - 1)

class RequestThrottler:
    def __init__(self, requests_per_minute):
        self.requests_per_minute = requests_per_minute
        self.interval = 60 / requests_per_minute
        self.last_request_time = 0

    def wait(self):
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.interval:
            time.sleep(self.interval - time_since_last_request)
        self.last_request_time = time.time()

def get_browser_like_headers():
    browser_versions = {
        'chrome': ['91.0.4472.124', '92.0.4515.107', '93.0.4577.63'],
        'firefox': ['89.0', '90.0', '91.0'],
        'safari': ['14.1.2', '15.0', '15.1']
    }
    
    browser = random.choice(list(browser_versions.keys()))
    version = random.choice(browser_versions[browser])
    
    if browser == 'chrome':
        user_agent = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36'
    elif browser == 'firefox':
        user_agent = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}'
    else:  # safari
        user_agent = f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15'

    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    return headers

def create_session():
    session = cloudscraper.create_scraper()
    session.headers.update(get_browser_like_headers())
    return session

session_pool = []

def create_session_pool(pool_size=5):
    global session_pool
    session_pool = [create_session() for _ in range(pool_size)]

def get_random_session():
    global session_pool
    if not session_pool:
        create_session_pool()
    return random.choice(session_pool)

def refresh_session_pool():
    global session_pool
    session_pool = [create_session() for _ in session_pool]

def adaptive_delay(min_delay=5, max_delay=15, error_delay=30):
    base_delay = random.uniform(min_delay, max_delay)
    jitter = random.uniform(-1, 1)
    return max(0.1, base_delay + jitter)

def get_total_pages(soup):
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

def fetch_listing_urls(main_url, proxy_manager, throttler):
    listings = []
    current_page = 1
    max_retries = 3
    today_date = datetime.now().strftime("%Y-%m-%d")
    filename = f'listings_{today_date}.csv'

    while True:
        print(f"Scraping page {current_page} for URLs...")
        try:
            session = get_random_session()
            proxy = proxy_manager.get_proxy()
            session.proxies = {"http": proxy, "https": proxy}
            
            throttler.wait()
            response = session.get(main_url)
            response.raise_for_status()
            
            proxy_manager.mark_success(proxy)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if current_page == 1:
                total_pages = get_total_pages(soup)
                print(f"Total pages to scrape: {total_pages}")

            for listing in soup.find_all('div', class_='listing-block'):
                link_tag = listing.find('a', class_='listing-block__link')
                if link_tag:
                    title = link_tag.find('span', class_='listing-block__title').text.strip() if link_tag else 'N/A'
                    link = "https://www.agriaffaires.co.uk" + link_tag.get('href', 'N/A')
                    print(f"Found listing: {title}, URL: {link}")
                    
                    if link != 'N/A':
                        listings.append({
                            'Title': title,
                            'URL': link
                        })

            save_data_to_csv(listings, filename)

            if current_page >= total_pages:
                print("Reached the last page.")
                break

            current_page += 1
            next_page_url = f"https://www.agriaffaires.co.uk/used/farm-tractor/{current_page}/4044/massey-ferguson.html"
            main_url = next_page_url
            time.sleep(adaptive_delay())

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            proxy_manager.mark_failed(proxy)
            max_retries -= 1
            if max_retries == 0:
                print("Max retries reached. Saving data and stopping scraper.")
                save_data_to_csv(listings, filename)
                break
            time.sleep(adaptive_delay(error_delay=30))

        except (CloudflareChallengeError, CloudflareCaptchaError) as e:
            print(f"Error fetching listings due to Cloudflare challenge: {e}")
            save_data_to_csv(listings, filename)
            break

    return listings

def fetch_listing_details(url, proxy_manager, throttler):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            session = get_random_session()
            proxy = proxy_manager.get_proxy()
            session.proxies = {"http": proxy, "https": proxy}
            
            throttler.wait()
            response = session.get(url)
            response.raise_for_status()
            
            proxy_manager.mark_success(proxy)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            price = 'N/A'
            price_tag = soup.find('div', class_='price txtcenter')
            if price_tag:
                price_value = price_tag.find('span', class_='js-priceToChange')
                currency_value = price_tag.find('span', class_='js-currencyToChange')
                if price_value and currency_value:
                    price = f"{price_value.text.strip()} {currency_value.text.strip()}"
            
            dealer = location = 'N/A'
            dealer_info = soup.find('div', class_='item-fluid item-center')
            if dealer_info:
                dealer_name_tag = dealer_info.find('p', class_='u-bold h3-like man')
                if dealer_name_tag:
                    dealer = dealer_name_tag.text.strip()
                location_tag = dealer_info.find('div', class_='u-bold')
                if location_tag:
                    location = location_tag.text.strip()

            phone_numbers = []
            phone_list = soup.find('ul', id='js-dropdown-phone-2')
            if phone_list:
                for phone_tag in phone_list.find_all('a'):
                    phone_number = phone_tag.get('href', '').replace('tel://', '').strip()
                    phone_numbers.append(phone_number)
            
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
        except requests.exceptions.RequestException as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            proxy_manager.mark_failed(proxy)
            if attempt < max_retries - 1:
                time.sleep(adaptive_delay(error_delay=30))
            else:
                print(f"Failed to fetch details for {url} after {max_retries} attempts")
                return None

def main():
    proxy_list = [
        "https://ba13396172373555b0b863c3af19140f4c2ec41cf8b91c6c5515a81e694676912cd79502b3e422b5a0f9d816bab595b1-country-us-const-session-38d62:glby77lonnnr@zproxy.lum-superproxy.io:31112",
        "https://ba13396172373555b0b863c3af19140f4c2ec41cf8b91c6c5515a81e694676912cd79502b3e422b5a0f9d816bab595b1-country-us-const-session-38d63:glby77lonnnr@zproxy.lum-superproxy.io:31112",
        "https://ba13396172373555b0b863c3af19140f4c2ec41cf8b91c6c5515a81e694676912cd79502b3e422b5a0f9d816bab595b1-country-us-const-session-38d64:glby77lonnnr@zproxy.lum-superproxy.io:31112",
        "https://ba13396172373555b0b863c3af19140f4c2ec41cf8b91c6c5515a81e694676912cd79502b3e422b5a0f9d816bab595b1-country-us-const-session-38d65:glby77lonnnr@zproxy.lum-superproxy.io:31112",
        "https://ba13396172373555b0b863c3af19140f4c2ec41cf8b91c6c5515a81e694676912cd79502b3e422b5a0f9d816bab595b1-country-us-const-session-38d66:glby77lonnnr@zproxy.lum-superproxy.io:31112",
        "https://ba13396172373555b0b863c3af19140f4c2ec41cf8b91c6c5515a81e694676912cd79502b3e422b5a0f9d816bab595b1-country-us-const-session-38d67:glby77lonnnr@zproxy.lum-superproxy.io:31112",
    ]
    proxy_manager = ProxyManager(proxy_list)
    throttler = RequestThrottler(requests_per_minute=15)
    
    create_session_pool(5)
    
    main_url = 'https://www.agriaffaires.co.uk/used/farm-tractor/1/4044/massey-ferguson.html'

    listings = fetch_listing_urls(main_url, proxy_manager, throttler)

    detailed_listings = []
    for i, listing in enumerate(listings):
        print(f"Fetching details for listing {i+1}/{len(listings)}")
        detailed_info = fetch_listing_details(listing['URL'], proxy_manager, throttler)
        if detailed_info:
            detailed_listings.append({
                **listing,
                'Detailed Price': detailed_info.get('Price', 'N/A'),
                'Dealer': detailed_info.get('Dealer', 'N/A'),
                'Dealer Location': detailed_info.get('Location', 'N/A'),
                'Phone Numbers': detailed_info.get('Phone Numbers', []),
                'Specifications': detailed_info.get('Specifications', {})
            })
        time.sleep(adaptive_delay())

        if (i + 1) % 50 == 0:
            refresh_session_pool()

    today_date = datetime.now().strftime("%Y-%m-%d")
    filename = f'detailed_listings_{today_date}.csv'
    save_data_to_csv(detailed_listings, filename)

    if detailed_listings:
        print("Scraping completed successfully.")
    else:
        print("No listings found.")

if __name__ == "__main__":
    main()