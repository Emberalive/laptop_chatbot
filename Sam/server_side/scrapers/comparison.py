import re

from deepdiff import DeepDiff
import json
import pprint
import sys
import os
from loguru import logger
from datetime import datetime

logger.add(sys.stdout, format="{time} {level} {message}")
logger.add("../logs/comparison.log", rotation="10 MB", retention="35 days", compression="zip")
logger = logger.bind(user="comparer")

def get_old_path(directory='/home/samuel/laptop_chatbot/Sam/server_side/scrapers/scraped_data/old_data'):
    # regex to extract data from filename
    pattern = re.compile(r"scrape_(\d{4}-\d{2}-\d{2})\.json")
    latest_file = None
    latest_time = None

    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            timestamp_str = match.group(1)
            try:
                # parse to datetime (handles both date-only and date_time formats)
                dt = datetime(timestamp_str, "%Y-%m-%d")

                if not latest_time or dt > latest_time:
                    latest_time = dt
                    latest_file = filename
            except ValueError as e:
                logger.error(f"ValueError: {e}")
    if latest_file:
        return os.path.join(directory, latest_file)
    else :
        return None

def compare_new_and_old (old_path, new_path='/home/samuel/laptop_chatbot/Sam/server_side/scrapers/scraped_data/latest.json'):
    logger.info(f"starting the comparison between the od and new json files")
    try:
        with open(new_path) as f1, \
             open(old_path) as f2:
            data1 = json.load(f1)
            data2 = json.load(f2)

        diff = DeepDiff(data1, data2, verbose_level=2)

        if diff:
            logger.info("Differences found:")
            logger.info(pprint.pformat(diff))
            return diff
        else:
            logger.info("No differences found between the two files.")
            return None

    except Exception as e:
        logger.error(f"error in attempting to compare the old and new json data {e}")

latest_json_archive = get_old_path()

compare_new_and_old(latest_json_archive)