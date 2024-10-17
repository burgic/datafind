import cloudscraper
from cloudscraper.exceptions import CloudflareChallengeError, CloudflareCaptchaError
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime

def create_session():
    # Use cloudscraper to handle websites with Cloudflare
    session = cloudscraper.create_scraper()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

def fetch_listings(main_url, session):
    try:
        response = session.get(main_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        listings = []
        
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

        return listings
    
    except (CloudflareChallengeError, CloudflareCaptchaError) as e:
        print(f"Error fetching listings due to Cloudflare challenge: {e}")
        return []

def main():
    session = create_session()
    main_url = 'https://www.agriaffaires.co.uk/used/1/farm-tractor.html'
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
