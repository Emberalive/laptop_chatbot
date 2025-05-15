# Laptop Configuration Comparison and Sync Tool

This Python script compares two JSON files representing laptop configurations, identifies differences, and updates a PostgreSQL database accordingly. It is designed to detect newly added or removed laptop models and synchronize the database with those changes.

## Features

- Automatically identifies the latest old JSON file based on filename pattern.
- Compares it with the new JSON `latest.json` file using `DeepDiff`.
- Logs added and removed configurations.
- Inserts new data or deletes outdated configurations from a PostgreSQL database.
- Uses multithreading to optimize bulk insert operations.
- Structured logging using Loguru.

## Directory Structure

```
├── database_persistence_versions
│   ├── database_persistence-V1.py
│   └── database_persistence-V2.py
├── DBAccess
│   ├── database_persistence_V3.py
│   └── dbAccess.py
├── logs
│   ├── AI.log
│   ├── API.log
│   ├── comparison.log
│   ├── database.log
│   ├── scraper_1.log
│   ├── scraper_2.log
│   └── server.log
├── requirements.txt
└── scrapers
    ├── comparison.py
    ├── pyscraper1.py
    ├── pyscraper2.py
    └── scraped_data
        ├── laptop_links.txt
        ├── latest.json
        └── old_data
            ├── scrape_2025-05-06.json
            ├── scrape_2025-05-13.json
            ├── scrape_2025-05-14.json
            └── scrape_2025-05-15.json

```

## Environment Variables

Set the following variables in a `.env` file:

```env
OLD_JSON_DIR=path/to/old/json/files
NEW_JSON=path/to/new/json/file.json
```

## Dependencies

Install dependencies using:

```bash
pip install -r requirements.txt
```

Required packages include:

- deepdiff
- loguru
- python-dotenv
- psycopg2 (or psycopg2-binary)

## How It Works

1. **Detect Latest JSON File:** Locates the latest file in `OLD_JSON_DIR` using date-based filename pattern.
2. **Compare JSON Files:** Uses `DeepDiff` to find added and removed configurations.
3. **Database Sync:**
   - For **added** items: Inserts data into multiple tables, including laptops, features, ports, screens, CPUs, GPUs, and storage.
   - For **removed** items: Deletes configuration and associated records using the `config_id`.
4. **Parallel Inserts:** Bulk inserts into related tables are run in parallel using `ThreadPoolExecutor`.

## Running the Script independantly

Uncomment the last line in the script and run:

```bash
python compare_laptops.py
```

### It gets called through pyScraper2.py

```bash
python pyscraper2.py
```

## Logging

Logs are output to both the console and a log file (`logs/comparison.log`). Log rotation is handled automatically.

