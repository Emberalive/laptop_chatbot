import requests
from bs4 import BeautifulSoup
import os
import sys
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from loguru import logger

logger.add(sys.stdout, format="{time} {level} {message}")
logger.add("../logs/scraper.log", rotation="10 MB", retention="35 days", compression="zip")
logger = logger.bind(user="scraper_1")

def fetch_page_links(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        laptop_cards = soup.find_all('a', class_='card-wrap unstyled')
        
        current_links = set()
        for card in laptop_cards:
            href = card.get('href')
            if href:
                clean_link = urljoin("https://laptop-finder.co.uk", href.split('?')[0])
                current_links.add(clean_link)
        return current_links
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return set()

def scrape_laptops(base_url, output_file, max_pages=50, max_workers=5):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    output_directory = os.path.dirname(output_file)
    if output_directory and not os.path.exists(output_directory):
        os.makedirs(output_directory)

    link_lock = Lock()
    all_links = set()
    duplicate_detected = False

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for page in range(1, max_pages + 1):
            url = f"{base_url}&pagesize=96&page={page}"
            logger.info(f"Scheduling page {page}: {url}")
            futures[executor.submit(fetch_page_links, url, headers)] = page

        for future in as_completed(futures):
            page_number = futures[future]
            logger.info(f"Processing results from page {page_number}")
            page_links = future.result()

            if not page_links:
                logger.warning(f"No links found on page {page_number}.")
                continue

            with link_lock:
                if page_links in [all_links]:  # simple duplicate check
                    logger.warning(f"Duplicate page content detected on page {page_number}. Skipping.")
                    duplicate_detected = True
                    break
                all_links.update(page_links)

    with open(output_file, "w") as file:
        for link in sorted(all_links):
            file.write(link + "\n")

    logger.info(f"Total links scraped: {len(all_links)}")

if __name__ == "__main__":
    base_url = "https://laptop-finder.co.uk/?showoos=true&price_from=100&price_to=4900&screen_size_from=10&screen_size_to=18.4&memory_from=0&memory_to=128&storage_size_from=0&storage_size_to=6000&battery_life_from=2&battery_life_to=31"
    output_directory = "scraped_data"
    output_file = os.path.join(output_directory, "laptop_links.txt")

    scrape_laptops(base_url, output_file)
