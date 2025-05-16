
# Laptop Details Scraper

This script extracts detailed specifications, features, and pricing information for laptops from individual product pages listed on [laptop-finder.co.uk](https://laptop-finder.co.uk). It processes a list of URLs (scraped from an earlier stage) and saves structured data in JSON format.

## Features

- Parses HTML using BeautifulSoup to extract tables of data (e.g. specs, features, screen, ports).
- Grabs the first product image from the gallery.
- Scrapes price information from multiple sellers.
- Skips URLs already processed (resumable).
- Uses multithreading to scrape pages concurrently.

## Requirements

- `requests`
- `beautifulsoup4`

Install with:

```bash
pip install requests beautifulsoup4
```

## Usage

Ensure you have a file called `laptop_links.txt` inside the `scraped_data/` directory, containing one product URL per line (this can be generated using `pyscraper1.py`). Then simply run:

```bash
python pyscraper2.py
```

The script will output structured data to:

```
scraped_data/scraped_data.json
```

## Output Structure

The JSON file will contain an array of laptop entries, each with:
- `url`: source URL
- `tables`: list of data tables (e.g., product details, specs, features, screen, ports, prices)
  - Each table has a `title` and a dictionary or list of `data` entries

Example entry:

```json
    {
        "url": "https://laptop-finder.co.uk/info/18193/dell-latitude-3330-1rmd9-133-1920x1080-core-i5-115-1rmd9",
        "tables": [
            {
                "title": "Product Details",
                "data": {
                    "Brand": "Dell",
                    "Name": "Latitude 3330",
                    "Weight": "1.37 kg",
                    "image": "https://pcparts.uk/img.large.e7e099e0edfa48d22cd59877c5869763728a08172fab93f7a11a0cb7be5e1ab3.jpg"
                }
            },
            {
                "title": "Screen",
                "data": {
                    "Size": "13.3\"",
                    "Resolution": "1920x1080",
                    "Refresh Rate": "60 Hz",
                    "Touchscreen": true,
                    "Matte": true
                }
            },
            {
                "title": "Ports",
                "data": {
                    "HDMI": true,
                    "USB Type-C": true
                }
            },
            {
                "title": "Specs",
                "data": {
                    "Processor Brand": "Intel",
                    "Processor Name": "Core i5-1155G7",
                    "Graphics Card": "Intel Iris Xe Graphics eligible",
                    "Memory Installed": "8 GB",
                    "Storage": "256GB SSD"
                }
            },
            {
                "title": "Features",
                "data": {
                    "Operating System": "Windows 10 Professional",
                    "Backlit Keyboard": true,
                    "Numeric Keyboard": false,
                    "Bluetooth": true
                }
            },
            {
                "title": "Prices",
                "data": [
                    {
                        "shop_url": "https://laptop-finder.co.uk/product/go/4546633b-e463-4839-b5d6-9006b5dde39b",
                        "price": "£853.26"
                    },
                    {
                        "shop_url": "https://laptop-finder.co.uk/product/go/cd56b03d-5a88-4b8b-9e4c-4aa9fb80678c",
                        "price": "£1,038.46"
                    }
                ]
            }
        ]
    }
```

## Notes

- Invalid or failed pages are skipped gracefully with a warning.
- Existing JSON file is updated rather than overwritten.
- Only relevant fields are extracted from each table for clarity and consistency.
