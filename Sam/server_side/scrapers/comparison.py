import re
from deepdiff import DeepDiff
import json
import pprint
import sys
import os
from loguru import logger
from datetime import datetime

logger.remove()
logger.add(sys.stdout, format="{time} {level} {message}")
logger.add("../logs/comparison.log", rotation="10 MB", retention="35 days", compression="zip")
logger = logger.bind(user="comparer")

def get_old_path(directory='/home/samuel/laptop_chatbot/Sam/server_side/scrapers/scraped_data/old_data'):
    # regex to extract data from filename
    pattern = re.compile(r"scrape_(\d{4}-\d{2}-\d{2})\.json")
    logger.info(f"looking for filename patterns with {pattern}")
    latest_file = None
    latest_time = None

    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            timestamp_str = match.group(1)
            try:
                # parse to datetime (handles both date-only and date_time formats)
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d")

                if not latest_time or dt > latest_time:
                    latest_time = dt
                    latest_file = filename
            except ValueError as e:
                logger.error(f"ValueError: {e}")
    if latest_file:
        logger.info(f"found latest file: {os.path.join(directory, latest_file)}")
        return os.path.join(directory, latest_file)
    else:
        return None


# if the output says items have been removed, then the items are in the old file and not the new
# if the output says items have been added then the items are not in the old file, but they are in the new file
def compare_new_and_old (old_path, new_path='/home/samuel/laptop_chatbot/Sam/server_side/scrapers/scraped_data/latest.json'):
    logger.info(f"starting the comparison between the old: {old_path} and new: {new_path} json files")
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

def process_json_diff(diff_dict, action):
    models = []

    laptops = [diff_dict] if not isinstance(diff_dict, list) else diff_dict

    for laptop in laptops:
        # get the root key for the data changed
        if action == "added":
            logger.info(f"There are new items to be {action} to the database")
        else:
            logger.info(f"There are items to be {action} removed from the database")

        # getting the root key for the laptop
        root_key = next(
            (key for key in laptop.keys() if key.startswith("root[")), None
        )

        if not root_key:
            logger.warning(f"No root key found in json difference")
            continue
        else:
            logger.info(f"found the root key: {root_key}")

        root_data = laptop.get(root_key, {})
        tables = root_data.get('tables', [])
        num_tables = len(tables)

        if tables and isinstance(tables, list) and num_tables > 0:
            for table in tables:
                if isinstance(table, dict):
                    table_data = table.get('data', {})
                    if 'Name' in table_data:  # More explicit than table_data.get('Name')
                        models.append(table_data['Name'])
                elif isinstance(tables, list):
                    for item in table and 'Name' in table:
                        models.append(item['Name'])
                else:
                    logger.debug(f"Unexpected table data type: {type(table_data)}")

        else:
            logger.warning("No valid 'tables' data found in diff_added")
    logger.info(f"Laptop model(s) to be {action}: {models}")


def update_changes (json_diff_data):
        json_diff_added = json_diff_data.get('iterable_item_added')
        json_diff_removed = json_diff_data.get('iterable_item_removed')

        if json_diff_added:
            process_json_diff(json_diff_added, "added")
        elif json_diff_removed:
            process_json_diff(json_diff_removed, "removed")


latest_json_archive = get_old_path()
if latest_json_archive:
    logger.info(f"found old scrape {latest_json_archive}")
    try:
        json_diff = compare_new_and_old(latest_json_archive)
    except UnboundLocalError as e:
        logger.error(f"could not find an old path for the json data ERROR: {e}")
update_changes(json_diff)
