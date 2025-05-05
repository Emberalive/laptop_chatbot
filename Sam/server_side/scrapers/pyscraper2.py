import requests
from bs4 import BeautifulSoup
import json
import os
import sys
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from loguru import logger

logger.add(sys.stdout, format="{time} {level} {message}")
logger.add("../logs/scraper_2.log", rotation="10 MB", retention="35 days", compression="zip")
logger = logger.bind(user="scraper_2")

def scrape_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Get main image
        gallery_div = soup.find('div', id='details-gallery')
        first_image = None
        if gallery_div:
            first_image_link = gallery_div.find('a', class_='glightbox')
            if first_image_link:
                first_image = first_image_link.get('href')

        # Process tables
        details_div = soup.find('div', id='details-under')
        tables_data = []
        
        if details_div:
            product_details = {"title": "Product Details", "data": {}}
            specs_table = {"title": "Specs", "data": {}}
            features_table = {"title": "Features", "data": {}}

            for table_div in details_div.find_all('div'):
                table_title = table_div.find('span').get_text(strip=True) if table_div.find('span') else None
                table = table_div.find('table', class_='striped row-hover shadowable')
                if not table:
                    continue

                for row in table.find_all('tr'):
                    columns = row.find_all('td')
                    if len(columns) == 2:
                        title = columns[0].get_text(strip=True)
                        info = columns[1].get_text(strip=True)

                        if columns[1].find('i'):
                            if 'fa-check' in columns[1].find('i').get('class', []):
                                info = True
                            elif 'fa-times' in columns[1].find('i').get('class', []):
                                info = False

                        # Organize data
                        if table_title == "Product Details":
                            if title not in ["EAN", "MPN"]:
                                product_details['data'][title] = info
                        elif table_title == "Processor":
                            if title in ["Brand", "Name"]:  # Only keep these
                                specs_table['data'][f"Processor {title}"] = info
                        elif table_title == "Misc":
                            if title in ["Operating System", "Battery Life"]:
                                features_table['data'][title] = info
                            elif title in ["Graphics Card", "Memory Installed", "Storage"]:
                                specs_table['data'][title] = info
                        elif table_title == "Features":
                            features_table['data'][title] = info
                        elif table_title == "Screen":
                            if not any(t['title'] == "Screen" for t in tables_data):
                                tables_data.append({"title": "Screen", "data": {}})
                            next(t for t in tables_data if t['title'] == "Screen")['data'][title] = info
                        elif table_title == "Ports":
                            if not any(t['title'] == "Ports" for t in tables_data):
                                tables_data.append({"title": "Ports", "data": {}})
                            next(t for t in tables_data if t['title'] == "Ports")['data'][title] = info

            # Add image to product details
            if first_image:
                product_details['data']['image'] = first_image

            # Add organized tables
            if product_details['data']:
                tables_data.insert(0, product_details)
            if specs_table['data']:
                tables_data.append(specs_table)
            if features_table['data']:
                tables_data.append(features_table)

        # Always add prices table, even if empty
        prices_table = {"title": "Prices", "data": []}
        prices_div = soup.find('div', id='prices-under')
        if prices_div:
            price_table = prices_div.find('table', id='details-price-table')
            if price_table:
                price_entries = []
                for row in price_table.find_all('tr'):
                    columns = row.find_all('td')
                    if len(columns) == 3:
                        shop_link = columns[0].find('a')
                        if shop_link:
                            shop_url = urljoin("https://laptop-finder.co.uk", shop_link.get('href'))
                            price = columns[2].get_text(strip=True).replace('\u00a3', '£')
                            price_entries.append({'shop_url': shop_url, 'price': price})
                prices_table['data'] = price_entries

        tables_data.append(prices_table)

        return {
            'url': url,
            'tables': tables_data
        }

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None

def read_urls(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def save_scraped_data( directory="scraped_data/old_data"):
    latest_file = "scraped_data/latest.json"

    if not os.path.exists(latest_file):
        logger.error(f"{latest_file} does not exist. can not archive scraped data")
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            old_data = json.load(f)

        # create the directory if needed
        os.makedirs(directory, exist_ok=True)


        # create timestamped file path
        timestamp = datetime.now().strftime("%Y-%m-%d")
        file_name = f"scrape_{timestamp}.json"
        filepath = os.path.join(directory, file_name)

        # save archived data
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(old_data, file, indent=2, ensure_ascii= False)

        logger.info(f"Scrape saved to {filepath}")
    except Exception as e:
        logger.error(f"could not archive old data {e}")

def main():
    input_file = os.path.join("scraped_data", "laptop_links.txt")
    output_file = os.path.join("scraped_data", "latest.json")

    urls = read_urls(input_file)
    logger.info(f"Found {len(urls)} URLs to scrape")

    existing_data = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            logger.error("Warning: Existing output file contains invalid JSON")

    existing_urls = {item['url'] for item in existing_data if 'url' in item}
    urls_to_scrape = [url for url in urls if url not in existing_urls]

    scraped_data = []

    # Use ThreadPoolExecutor to scrape concurrently
    with ThreadPoolExecutor(max_workers=12) as executor:
        future_to_url = {executor.submit(scrape_url, url): url for url in urls_to_scrape}

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
                if data:
                    scraped_data.append(data)
                    logger.info(f"Scraped: {url}")
            except Exception as e:
                logger.error(f"Error with {url}: {e}")

    # save the old scraped data to an old directory
    save_scraped_data()

    # Save the combined data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data + scraped_data, f, indent=4, ensure_ascii=False)


    logger.info(f"Scraping complete. Total laptops scraped: {len(scraped_data)}")

if __name__ == "__main__":
    main()
