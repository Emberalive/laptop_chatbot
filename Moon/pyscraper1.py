import requests                                                                     # Import requests which sends HTTP requests
from bs4 import BeautifulSoup                                                       # Import BeautifulSoup which parses data from HTML content
import os                                                                           # Import the os module to handle file paths for saving data
from urllib.parse import urljoin                                                    # For clean URL joining

def scrape_laptops(base_url, output_file):                                          # Create function which passes two arguments
    page = 1                                                                        # Track page number during scraping
    previous_links = set()                                                          # Store links from the previous pages in an empty set to detect duplicates
    total_links_scraped = 0                                                         # Counter for total links scraped
    
    output_directory = os.path.dirname(output_file)                                 # Takes output_file dir path
    if output_directory and not os.path.exists(output_directory):                   # If dir path doesn't exist
        os.makedirs(output_directory)                                               # Create dir

    with open(output_file, "w") as file:                                            # Open output_file in "write mode"
        
        while True:
            url = f"{base_url}&pagesize=96&page={page}"                             # Construct URL for current page by appending page number to base url
            print(f"Scraping page {page}: {url}")                                   # Prints current page and URL being scraped

            try:                                                                    # Headers defines dictionary of HTTP headers to mimic real browser when requesting
            
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(url, headers=headers)                       # HTTP get request to URL using headers -> stores response
                response.raise_for_status()                                         # Response successful check

                soup = BeautifulSoup(response.text, 'html.parser')                  # Parse HTML content
                
                laptop_cards = soup.find_all('a', class_='card-wrap unstyled')      # Find all <a> tags with the specified class (they store the links we require)
                if not laptop_cards:                                                # If no laptop cards are found, stop scraping
                    print("No more pages found. Exiting.")
                    break

                current_links = set()                                               # Create empty set to store links scraped
                for card in laptop_cards:                                           # Iterates over each laptop card found
                    href = card.get('href')                                         # Extract href attribute (link we need)
                    if href:                                                        # If href not empty
                        # Clean the URL by removing query parameters and joining with base domain
                        clean_link = urljoin("https://laptop-finder.co.uk", href.split('?')[0])
                        current_links.add(clean_link)                               # Add the clean link to the current set

                if current_links == previous_links:                                 # Duplicate page detection
                    print("Detected duplicate page content. Exiting.")
                    break

                for link in current_links:                                          # Iterate over each link in the set
                    file.write(link + "\n")                                         # Write each link to the file

                total_links_scraped += len(current_links)                           # Update the total links scraped
                previous_links = current_links                                      # Update the previous_links set for the next iteration
                page += 1                                                           # Move to the next page

            except requests.exceptions.RequestException as e:                       # HTTP request exception catcher 
                print(f"Error fetching the website: {e}")
                break                                                               # Exit the loop if an error occurs

    print(f"Total links scraped: {total_links_scraped}")                            # Print the total number of links scraped

if __name__ == "__main__":                                                          # Main Execution 
    base_url = "https://laptop-finder.co.uk/?showoos=true&price_from=100&price_to=4200&screen_size_from=10&screen_size_to=18.4&memory_from=0&memory_to=128&storage_size_from=0&storage_size_to=6000&battery_life_from=2&battery_life_to=31"                                        # Base URL
    
    output_directory = "Moon"                                                       # Output dir
    output_file = os.path.join(output_directory, "laptop_links.txt")                # Create the full file path
    
    scrape_laptops(base_url, output_file)                                           # Call scraper function