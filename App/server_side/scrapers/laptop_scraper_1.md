
# Laptop Finder Web Scraper

This Python script scrapes laptop product page URLs from [laptop-finder.co.uk](https://laptop-finder.co.uk) using concurrent requests. It writes all unique product links to a specified output file.

## Features

- Scrapes laptop listing pages concurrently
- Extracts and deduplicates product URLs
- Handles pagination and duplicate content
- Outputs clean, sorted links to a file
- Configurable number of pages and workers

## Requirements

- Python 3.6+
- `requests`
- `beautifulsoup4`

Install dependencies:
```bash
pip install requests beautifulsoup4
```

## How It Works

1. Iterates through a configurable number of pages.
2. Extracts valid product links using `BeautifulSoup`.
3. Detects and skips duplicate pages.
4. Writes the collected links to `scraped_data/laptop_links.txt`.

## Usage

Run the script with:
```bash
python laptop_scraper.py
```

## Script Parameters

- `base_url`: Filtered URL for laptops.
- `output_file`: Path to the output `.txt` file.
- `max_pages`: Number of pages to scrape (default: 50).
- `max_workers`: Number of threads to use (default: 5).

You can customize the `base_url` query parameters to adjust filtering options like price, screen size, storage, etc.

## File Output

All scraped URLs are saved to:
```
scraped_data/laptop_links.txt
```

## Example Output

```
https://laptop-finder.co.uk/product/12345
https://laptop-finder.co.uk/product/67890
...
```

## Notes

- If a page returns the same set of product links as a previous one, scraping stops early to avoid duplicate processing.
- Ensure the website allows scraping and respect their [robots.txt](https://laptop-finder.co.uk/robots.txt) policy.

## License

This script is provided for educational purposes only.
