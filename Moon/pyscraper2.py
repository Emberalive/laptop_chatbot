import requests                                                                            # Requests web pages                               
from bs4 import BeautifulSoup                                                              # Parses HTML content
import json                                                                                # Handles JSON data
import os                                                                                  # Manages File Paths

def scrape_url(url):
    try:
        headers = {                                                                        # Mimics a browser
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)                                      # Gets webpage
        response.raise_for_status()                                                        # Error checks

        soup = BeautifulSoup(response.text, 'html.parser')                                 # Parses HTML content

        details_div = soup.find('div', id='details-under')                                 # Finds the Details section which holds information required
        tables_data = []
        if details_div:
            tables = details_div.find_all('div')
            
            for table_div in tables:                                                       # Returns table titles and skips empty tables
                
                table_title = table_div.find('span').get_text(strip=True) if table_div.find('span') else "Untitled Table"
                table = table_div.find('table', class_='striped row-hover shadowable')
                if not table:
                    continue

                rows = table.find_all('tr')                                                # Processes each row of the tables
                table_info = {}
                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) == 2:
                        title = columns[0].get_text(strip=True)
                        info = columns[1].get_text(strip=True)

                        if columns[1].find('i'):                                           # Converts checkmarks and crosses to True and False
                            if 'fa-check' in columns[1].find('i').get('class', []):
                                info = True
                            elif 'fa-times' in columns[1].find('i').get('class', []):
                                info = False

                        table_info[title] = info

                tables_data.append({                                                       # Stores table data
                    'title': table_title,
                    'data': table_info
                })

        prices_div = soup.find('div', id='prices-under')                                   # extracts shop URLs 
        extra_info = []
        if prices_div:
            price_table = prices_div.find('table', id='details-price-table')
            if price_table:
                rows = price_table.find_all('tr')
                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) == 3:
                        shop_link = columns[0].find('a')
                        shop_url = "https://laptop-finder.co.uk" + shop_link.get('href') if shop_link else None
                        price = columns[2].get_text(strip=True).replace('\u00a3', '£')

                        extra_info.append({                                                # Stores shop and price data
                            'shop_url': shop_url,
                            'price': price
                        })

        gallery_div = soup.find('div', id='details-gallery')                               # Returns the first image in the highest resolution
        first_image = None
        if gallery_div:
            first_image_link = gallery_div.find('a', class_='glightbox')
            if first_image_link:
                first_image = first_image_link.get('href')

        return {                                                                           # Returns all scraped data required
            'url': url,
            'tables': tables_data,
            'extra-info': extra_info,
            'image': first_image
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
                                                                                            # !!!!!!!! HELPER FUNCTIONS AND MAIN BELOW !!!!!!!!

def read_urls(file_path):                                                                  # Reads laptop URLs from Laptop_Links.txt
    with open(file_path, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
    return urls

def load_existing_data(file_path):                                                         # Loads existing JSON data (If any available)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as json_file:
                return json.load(json_file)
        except json.JSONDecodeError:
            print(f"Warning: {file_path} contains invalid JSON. Starting with an empty list.")
            return []
    return []

def save_to_json(data, file_path):                                                         # Saves new data to JSON with proper formatting
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json_file.write(json_str)

def main():                                                                                # Main Function
    input_file = os.path.join("Moon", "laptop_links.txt")
    output_file = os.path.join("Moon", "scraped_data.json")

    urls = read_urls(input_file)
    print(f"Found {len(urls)} URLs to scrape.")

    existing_data = load_existing_data(output_file)
    existing_urls = {item['url'] for item in existing_data}

    scraped_data = []

    for url in urls:
        if url in existing_urls:
            print(f"Skipping already scraped URL: {url}")
            continue

        print(f"Scraping: {url}")
        data = scrape_url(url)
        if data:
            scraped_data.append(data)

    combined_data = existing_data + scraped_data
    save_to_json(combined_data, output_file)
    print(f"Scraping completed. Data saved to {output_file}")

if __name__ == "__main__":                                                                 # Run
    main()