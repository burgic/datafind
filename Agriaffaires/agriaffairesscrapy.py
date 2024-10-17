import scrapy
import random
from datetime import datetime
import os
import pandas as pd

class AgriaffairesSpider(scrapy.Spider):
    name = 'agriaffaires_spider'
    allowed_domains = ['agriaffaires.co.uk']
    start_urls = ['https://www.agriaffaires.co.uk/used/farm-tractor/1/4044/massey-ferguson.html']

    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # To prevent getting blocked, adjust as necessary
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 5
    }

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
 
    ]

    def get_random_user_agent(self):
        return random.choice(self.user_agents)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                headers={'User-Agent': self.get_random_user_agent()},
                callback=self.parse
            )

    def parse(self, response):
        listings = []
        current_page = response.url.split('/')[-3]
        
        # Extract listing blocks
        for listing in response.css('div.listing-block'):
            title = listing.css('a.listing-block__link span.listing-block__title::text').get()
            link = listing.css('a.listing-block__link::attr(href)').get()
            full_url = response.urljoin(link)

            if full_url and title:
                listings.append({
                    'Title': title.strip(),
                    'URL': full_url.strip(),
                })
                # Yield detailed data for each listing
                yield scrapy.Request(
                    url=full_url,
                    headers={'User-Agent': self.get_random_user_agent()},
                    callback=self.parse_listing_details,
                    meta={'basic_info': {'Title': title, 'URL': full_url}}
                )
        
        # Save the basic listings after each page
        today_date = datetime.now().strftime("%Y-%m-%d")
        filename = f'listings_{today_date}_page_{current_page}.csv'
        self.save_data_to_csv(listings, filename)

        # Pagination: Check if there's a next page
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(
                url=next_page_url,
                headers={'User-Agent': self.get_random_user_agent()},
                callback=self.parse
            )

    def parse_listing_details(self, response):
        basic_info = response.meta.get('basic_info', {})
        
        # Extract price
        price = response.css('div.price span.js-priceToChange::text').get()
        currency = response.css('div.price span.js-currencyToChange::text').get()
        full_price = f"{price.strip()} {currency.strip()}" if price and currency else 'N/A'
        
        # Extract dealer and location information
        dealer = response.css('div.item-fluid.item-center p.u-bold.h3-like.man::text').get(default='N/A').strip()
        location = response.css('div.item-fluid.item-center div.u-bold::text').get(default='N/A').strip()

        # Extract phone numbers
        phone_numbers = response.css('ul#js-dropdown-phone-2 a::attr(href)').re(r'tel://(.*)')
        
        # Extract specifications
        specs = {}
        for row in response.css('table.table--specs tr'):
            key = row.css('td:first-child::text').get(default='').strip().replace(':', '')
            value = row.css('td:last-child::text').get(default='').strip()
            specs[key] = value
        
        # Combine basic and detailed info
        detailed_listing = {
            'Title': basic_info['Title'],
            'URL': basic_info['URL'],
            'Price': full_price,
            'Dealer': dealer,
            'Location': location,
            'Phone Numbers': phone_numbers,
            'Specifications': specs,
        }

        # Save detailed listings to a CSV file
        today_date = datetime.now().strftime("%Y-%m-%d")
        filename = f'detailed_listings_{today_date}.csv'
        self.save_data_to_csv([detailed_listing], filename)

    def save_data_to_csv(self, listings, filename):
        output_dir = './results'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        df = pd.DataFrame(listings)
        if not os.path.isfile(filepath):
            df.to_csv(filepath, index=False)
        else:
            df.to_csv(filepath, mode='a', header=False, index=False)
        self.logger.info(f"Data saved to {filepath}")
