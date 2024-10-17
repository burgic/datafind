import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import random
from datetime import datetime

def create_session():
    session = requests.Session()
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
        for listing in soup.find_all('a', class_='listing-block__link'):
            title = listing.find('span', class_='listing-block__title').text.strip()
            link = "https://www.agriaffaires.co.uk" + listing['href']
            
            listings.append({
                'Title': title,
                'URL': link
            })

        return listings
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching listings: {e}")
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
