import requests
from bs4 import BeautifulSoup

def scrape_laptops(base_url):
    page = 1
    previous_links = set()  # Store links from the previous page to detect duplicates

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

            # Collect links from the current page
            current_links = set()
            for card in laptop_cards:
                href = card.get('href')  # Get the href attribute
                if href:  # Ensure the href is not empty
                    full_link = base_url + href  # Construct the full URL
                    current_links.add(full_link)  # Add the link to the current set

            # Check if the current page's links are the same as the previous page's links
            if current_links == previous_links:
                print("Detected duplicate page content. Exiting.")
                break

            # Print the links from the current page
            for link in current_links:
                print(link)

            # Update the previous_links set for the next iteration
            previous_links = current_links

            # Move to the next page
            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching the website: {e}")
            break

if __name__ == "__main__":
    base_url = "https://laptop-finder.co.uk"
    scrape_laptops(base_url)