
# Laptop JSON Processor and Database Inserter

This script reads a JSON file of scraped laptop data and bulk-inserts the relevant information into a PostgreSQL database using multithreading for improved performance.

---

## Features

- Parses structured JSON data for laptops
- Inserts:
  - CPU and GPU information
  - Laptop models and configurations
  - Specifications (e.g., ports, screens, features, storage)
- Uses bulk operations and thread pools for speed
- Maintains data integrity with ON CONFLICT logic
- Logs actions and errors to both console and a rotating file log inside path `logs/server.log`

---

## File Structure

```
├── database_persistence-V1.py
├── database_persistence-V2.py
├── database_persistence-V3.py
├── DBAccess
│   ├── dbAccess.py
│   └── __pycache__
│       ├── dbAccess.cpython-310.pyc
│       ├── dbAccess.cpython-311.pyc
│       └── dbAccess.cpython-312.pyc
├── images
│   ├── image_insertion.py
│   ├── image_selection.py
│   ├── imageStock.jpg
│   └── saved_image.jpg
├── logs
│   ├── output.2025-05-01_19-59-35_897040.log.zip
│   ├── output.log
│   └── server.log
├── monthly_run.py
├── out
│   └── output_log.log
├── requirements.txt
├── run_all.py
└── scrapers
    ├── pyscraper1.py
    ├── pyScraper1.py
    ├── pyscraper2.py
    ├── pyScraper2.py
    └── scraped_data
        ├── laptop_links.txt
        └── scraped_data.json

```

---

## Requirements

- Python 3.8+
- PostgreSQL database
- Dependencies:
  - `loguru`
  - `psycopg2` or compatible DB API
  - `concurrent.futures` (standard lib)

Install with:

```bash
pip install -r requirments.txt
```

---

## Usage

1. **Ensure your JSON data exists** in one of the fallback paths defined in the script.
2. **Configure your database connection** in `DBAccess/dbAccess.py`.
3. **Run the script:**

```bash
python database_persistence-V3.py
```

The script will:
- Load laptop data from JSON
- Extract and normalize relevant data
- Perform bulk inserts into multiple database tables

---

## Notes

- Bulk inserts use `executemany()` for efficiency.
- A model lookup dictionary is created to resolve foreign key relationships.
- Each thread-safe function uses its own cursor.
- The logger writes to both stdout and a compressed log file with rotation.

---

## Performance

This script has been optimized over several versions:
- Initial runtime: ~14 minutes
- Current runtime: ~3:45

Speedups achieved via:

### Thread pools
```
I have added ThreadPoolExecutor for when i am bulk inserting, so that each table (ports, features, storage, screen) is inserted 
at the same time, making the process faster
```
### Cursor management

```
Instead of initializing a new connection for each insert query as well as commiting and rolling back on each function I have
created a global connectiona and cursor usig the database access script. I then passed through the global connection into each
function and created a new cursor for the function (this is also because cursors are not thread safe)
```
### JSON path fallbacks
```
This isnt necessarily speed of execution, but it allows me to not have to worry aboout changing the path depending on the machine that 
I am using to test or run the script, as there are at least 3 devices that I will be using to edit the script
```

### Reduced logging to stdout
```
I have  massivley reduced the output to system, by being able to bulk insert, as i dont need to (and cant) log every time i insert
one set of values, this reduces time as there is no slight hanging to wait for the system output to occur
```


## To-Do / Improvements

- Add unit tests for individual insert functions
- Include a config file for JSON paths
- create a dotenv file for sensitive information
- Dockerize the script with environment-based DB credentials

---

## Author

Samuel  
University of Brighton | Group Project Laptop ChatBot  
2025
