# Laptop Recommendation App

## Overview

This application recommends laptops to users based on their natural language input. It leverages a Sentence Transformer model on the backend to interpret user requirements and match them with the most suitable laptops in the database. The front end is built using **Nuxt.js**, and the backend is written in **Python**.

## Features

* **Natural Language Recommendations**: Users input their needs in plain English, and the app returns laptop suggestions.
* **Monthly Data Updates**: The database is updated monthly by re-scraping laptop data and comparing the latest scrape with previous datasets.
* **REST API**: A clean and structured API connects the Nuxt front end to the Python backend.

---

## Directory Structure

```
server_side/
├── DBAccess
│   ├── database_persistence_V3.py
│   ├── dbAccess.py
│   └── __pycache__/
│       ├── database_persistence_V3.cpython-311.pyc
│       ├── database_persistence_V3.cpython-312.pyc
│       ├── dbAccess.cpython-310.pyc
│       ├── dbAccess.cpython-311.pyc
│       └── dbAccess.cpython-312.pyc
├── language_transformer
│   ├── chatBotAPI3.py
│   ├── __pycache__/
│   │   ├── chatBotAPI3.cpython-311.pyc
│   │   └── STPrototype3.cpython-311.pyc
│   └── STPrototype3.py
├── logs
|
├── requirements.txt
└── scrapers
    ├── comparison.py
    ├── comparison_ReadMe.md
    ├── laptop_scraper_1.md
    ├── laptop_scraper_2.md
    ├── __pycache__/
    │   ├── comparison.cpython-311.pyc
    │   ├── comparison.cpython-312.pyc
    │   └── pyscraper2.cpython-312.pyc
    ├── pyscraper1.py
    ├── pyscraper2.py
    └── scraped_data/
        ├── laptop_links.txt
        ├── latest.json
        └── old_data/
            ├── scrape_2025-05-06.json
            ├── scrape_2025-05-13.json
            └── scrape_2025-05-14.json
```

---

## Tech Stack

### Front End:

* **Nuxt.js**
* Vue 3 / Composition API
* Axios (for API communication)

### Back End:

* **Python 3.11+**
* **Sentence Transformers** (HuggingFace)
* **FastAPI** (or Flask for simpler APIs)

### Scraping & Data:

* Custom Python scripts using libraries like `requests`, `BeautifulSoup4`
* Data saved as JSON
* Monthly comparison logic via `comparison.py`

---

## How It Works

1. **User Input**: User submits a query like "I want a lightweight laptop for travel with good battery life."
2. **Sentence Embedding**: Backend transforms the input into an embedding vector using a Sentence Transformer.
3. **Similarity Matching**: The model compares the user vector with precomputed embeddings of scraped laptop specs.
4. **Recommendation**: Top matching laptops are returned via API and displayed in the Nuxt frontend.

---

## Monthly Update Workflow

1. **Scrapers** (`pyscraper1.py` & `pyscraper2.py`) collect new laptop listings.
2. **Comparison** (`comparison.py`) compares `latest.json` with files in `old_data/`.
3. **Database Update**: Any new or changed entries are updated in the database.

---

## Installation & Setup

### Backend

```bash
cd server_side
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Logs

Logs are stored under the `logs/` directory to track scraper runs, database updates, and server/API activity.

---

## Notes

* Backend is modularized with separate layers for scraping, data persistence, and language understanding.

---

## License

MIT License. See `LICENSE` file for more details.

---

## Maintainer

This project is maintained by the original author(s). For bugs or feature requests, please create an issue.
