import requests
from bs4 import BeautifulSoup

def scrape_laptops(base_url):
    page = 1
    while True:
        # Construct the URL for the current page
        url = f"{base_url}?pagesize=96&page={page}"
        print(f"Scraping page {page}: {url}")

        try:
            # Fetch the HTML content
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract links
            laptop_cards = soup.find_all('a', class_='card-wrap unstyled')  # Find all <a> tags with the specified class
            if not laptop_cards:  # If no laptop cards are found, stop scraping
                print("No more pages found. Exiting.")
                break

            for card in laptop_cards:
                href = card.get('href')  # Get the href attribute
                if href:  # Ensure the href is not empty
                    full_link = base_url + href  # Construct the full URL
                    print(full_link)  # Print the full link

            # Move to the next page
            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching the website: {e}")
            break

if __name__ == "__main__":
    base_url = "https://laptop-finder.co.uk"
    scrape_laptops(base_url)