import requests
from bs4 import BeautifulSoup

def scrape_laptops(url):
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
        base_url = "https://laptop-finder.co.uk"
        laptop_cards = soup.find_all('a', class_='card-wrap unstyled')  # Find all <a> tags with the specified class
        for card in laptop_cards:
            href = card.get('href')  # Get the href attribute
            if href:  # Ensure the href is not empty
                full_link = base_url + href  # Construct the full URL
                print(full_link)  # Print the full link

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the website: {e}")

if __name__ == "__main__":
    url = "https://laptop-finder.co.uk"
    scrape_laptops(url)