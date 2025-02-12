import requests
from bs4 import BeautifulSoup
import json
import os

def scrape_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Locate the div containing all tables
        details_div = soup.find('div', id='details-under')
        if not details_div:
            print(f"No 'details-under' div found in {url}")
            return None

        # Extract all tables within the div
        tables = details_div.find_all('div')  # Each table is inside a <div>
        if not tables:
            print(f"No tables found in {url}")
            return None

        # Store the extracted data
        table_data = []

        for table_div in tables:
            table_title = table_div.find('span').get_text(strip=True) if table_div.find('span') else "Untitled Table"
            table = table_div.find('table', class_='striped row-hover shadowable')
            if not table:
                continue

            rows = table.find_all('tr')  # Find all rows in the table
            table_info = {}

            for row in rows:
                columns = row.find_all('td')  # Find all columns in the row
                if len(columns) == 2:  # Ensure there are exactly two columns
                    title = columns[0].get_text(strip=True)  # First column is the title
                    info = columns[1].get_text(strip=True)   # Second column is the info

                    # Handle boolean values (check for <i> tags)
                    if columns[1].find('i'):
                        if 'fa-check' in columns[1].find('i').get('class', []):
                            info = True
                        elif 'fa-times' in columns[1].find('i').get('class', []):
                            info = False

                    table_info[title] = info

            table_data.append({
                'title': table_title,
                'data': table_info
            })

        return {
            'url': url,
            'tables': table_data
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def read_urls(file_path):
    with open(file_path, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
    return urls

def load_existing_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as json_file:
            return json.load(json_file)
    return []

def save_to_json(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def main():
    input_file = os.path.join("Moon", "laptop_links.txt")
    output_file = os.path.join("Moon", "scraped_data.json")

    urls = read_urls(input_file)
    print(f"Found {len(urls)} URLs to scrape.")

    # Load existing data to check for duplicates
    existing_data = load_existing_data(output_file)
    existing_urls = {item['url'] for item in existing_data}  # Set of already scraped URLs

    scraped_data = []

    for url in urls:
        if url in existing_urls:
            print(f"Skipping already scraped URL: {url}")
            continue

        print(f"Scraping: {url}")
        data = scrape_url(url)
        if data:
            scraped_data.append(data)

    # Combine existing data with newly scraped data
    combined_data = existing_data + scraped_data

    # Save the combined data to the JSON file
    save_to_json(combined_data, output_file)
    print(f"Scraping completed. Data saved to {output_file}")

if __name__ == "__main__":
    main()