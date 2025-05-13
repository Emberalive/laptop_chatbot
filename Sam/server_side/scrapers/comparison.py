import re
from concurrent.futures import ThreadPoolExecutor

from deepdiff import DeepDiff
import json
import pprint
import sys
import os
from loguru import logger
from datetime import datetime
from DBAccess.dbAccess import get_db_connection, release_db_connection, init_db_pool
from DBAccess.database_persistence_V3 import insert_configuration, insert_laptop_model,  insert_gpu_records, insert_cpu_records,  bulk_insert_storage, bulk_insert_features,  bulk_insert_ports, bulk_insert_screens
from dotenv import load_dotenv
load_dotenv()

logger.remove()

# Ensure the logs directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)

logger.add(sys.stdout, format="{time} {level} {message}")
logger.add(os.path.join(os.path.dirname(__file__), "logs", "comparison.log"),
           rotation="10 MB", retention="35 days", compression="zip")
logger = logger.bind(user="comparer")

def get_old_path(directory=os.getenv('OLD_JSON_DIR')):
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
def compare_new_and_old (old_path, new_path=os.getenv('NEW_JSON')):
    logger.info(f"starting the comparison between the old: {old_path} and new: {new_path} json files")
    try:
        with open(new_path) as f1, \
             open(old_path) as f2:
            data1 = json.load(f1)
            data2 = json.load(f2)

        diff = DeepDiff(data1, data2, verbose_level=2)

        if diff:
            logger.info("Differences found:")
            logger.info(pprint.pprint(diff))
            return diff
        else:
            logger.info("No differences found between the two files.")
            return None

    except Exception as e:
        logger.error(f"error in attempting to compare the old and new json data {e}")


def process_json_diff(diff_dict, action, json_conn):
    models = []

    laptop_model_records = []
    feature_records = []
    ports_records = []
    storage_records = []
    screen_records = []
    gpu_records = []
    cpu_records = []

    logger.info(f"Processing {action} items")

    # Handle case where we get the inner dict directly
    if not any(key.startswith("root[") for key in diff_dict.keys()):
        diff_dict = {'root[0]': diff_dict}  # Wrap in a root key if needed

    # Process each laptop (each root[ID] entry)
    for root_key, laptop_data in diff_dict.items():
        if not root_key.startswith("root["):
            continue

        logger.debug(f"Processing laptop: {root_key}")
        tables = laptop_data.get('tables', [])

        # Initialize variables
        model_id = weight = memory = o_s = battery_life = laptop_price = None
        laptop_model = laptop_brand = laptop_image = None
        storage_type = storage_capacity = None
        back_lit = num_pad = bluetooth = None
        ethernet = hdmi = usb_type_c = thunderbolt = display_port = None
        size = resolution = touch_screen = refresh_rate = None
        cpu_brand = cpu_name = gpu_model = gpu_brand = None


        if tables and isinstance(tables, list) and action == "added":
            for table in tables:
                table_data = table.get('data', {})  # Get the data dictionary
                table_title = table.get('title', '')  # Fixed: use () not []

                if table_title == "Product Details":
                    laptop_model = table_data.get('Name', '')
                    laptop_brand = table_data.get('Brand', '')
                    weight = table_data.get('Weight', '')
                    laptop_image = table_data.get('image_url', '')
                elif table_title == "Specs":
                    cpu_name = table_data.get('Processor Name', '')
                    cpu_brand = table_data.get('Processor Brand')
                    gpu_info = table_data.get('Graphics Card', '')
                    memory = table_data.get('Memory Installed', '')
                    storage = table_data.get('Storage', '')
                    storage_info = storage.split(" ")
                    storage_capacity = storage_info[0] if storage_info else 'none'
                    storage_type = storage_info[1].strip().upper() if len(storage_info) > 1 else 'none'



                    gpu_components = gpu_info.split(" ")
                    gpu_brand = gpu_components[0] if gpu_components else "Unknown"
                    gpu_model = " ".join(gpu_components[1:]) if len(gpu_components) > 1 else "Unknown"

                elif table_title == "Features":
                    o_s = table_data.get('Operating System', 'Not Specified')
                    battery_life = table_data.get('Battery Life', 'Unknown')
                    back_lit = table_data.get('Backlit Keyboard', False)
                    bluetooth = table_data.get('Bluetooth', False)
                    num_pad = table_data.get('Numeric Keyboard', False)
                    thunderbolt = table_data.get('Thunderbolt', False)
                    display_port = table_data.get('Display Port', False)
                elif table_title == 'Screen':
                    resolution = table_data.get('Resolution')
                    size = table_data.get('Size')
                    touch_screen = table_data.get('Touchscreen')
                    refresh_rate = table_data.get('Refresh Rate')
                elif table_title == 'Ports':
                    ethernet = table_data.get('Ethernet', False)
                    hdmi = table_data.get('HDMI', False)
                    usb_type_c = table_data.get('USB Type-C', False)
                elif table_title == 'Prices':
                    #checking if the prices object is empty or is a list, if its empty then no actual value is got, and if its not
                    #empty then it is gathered.
                    if isinstance(table_data, list) and len(table_data) > 0:
                        first_entry = table_data[0]
                        laptop_price = first_entry.get('price', 'No Price available')
                        laptop_shop_url = first_entry.get('shop_url', 'No Shop available')
                    else:
                        laptop_price = 'No Price available'
                        laptop_shop_url = 'No Shop available'

            model_id = get_model_id(laptop_model)

            if not model_id:
                laptop_model_records.append((laptop_brand, laptop_model, laptop_image))
                model_look_up = insert_laptop_model(laptop_model_records, json_conn)
                model_id = model_look_up.get(laptop_model)

            if laptop_model:
                logger.info(f"Laptop details for {laptop_model}:\n"
                            f"--------------------------------------------------------------------------------\n"
                            f"model_id = {model_id}\n"
                            f"Weight: {weight}\n"
                            f"Processor: {cpu_name}\n"
                            f"Graphics card: {gpu_model}\n"
                            f"Memory: {memory}\n"
                            f"OS: {o_s}\n"
                            f"Battery: {battery_life}\n")
                models.append(laptop_model)

                config_id = insert_configuration(model_id, laptop_price, weight, battery_life, memory, o_s, cpu_name, gpu_model, json_conn)
                if not config_id or config_id is None:
                    logger.warning("laptop configuration already exists, moving to the next possible insert if any")
                    continue

                logger.info(f"Inserted configuration with config_id: {config_id}")
                if config_id is None:
                    storage_records.append((config_id, storage_type, storage_capacity))
                    feature_records.append((config_id, back_lit, num_pad, bluetooth))
                    ports_records.append((config_id, ethernet, hdmi, usb_type_c, thunderbolt, display_port))
                    screen_records.append((config_id, size, resolution, touch_screen, refresh_rate))

                    cpu_records.append((cpu_brand, cpu_name))
                    gpu_records.append((gpu_brand, gpu_model))
                else:
                    logger.error(f"Failed to insert configuration for model_id {model_id}. Skipping associated data.")


        else:
            logger.warning(f"No valid tables found for {root_key}")

    if models:
        logger.info(f"Laptop model(s) to {action}: {models}")
    else:
        logger.warning(f"No laptop models found in {action} items")

    if cpu_records and gpu_records and storage_records is None:
        logger.info("There are no records to insert, Exiting the script")
        exit
    insert_cpu_records(cpu_records, json_conn)
    insert_gpu_records(gpu_records, json_conn)

    with ThreadPoolExecutor(max_workers=11) as executor:
        # Get one connection per thread
        storage_conn, storage_cur= get_db_connection()
        features_conn, features_cur = get_db_connection()
        ports_conn, ports_cur= get_db_connection()
        screens_conn, screens_cur = get_db_connection()

        futures = [
            executor.submit(bulk_insert_storage, storage_records, storage_conn),
            executor.submit(bulk_insert_features, feature_records, features_conn),
            executor.submit(bulk_insert_ports, ports_records, ports_conn),
            executor.submit(bulk_insert_screens, screen_records, screens_conn)
        ]

        # wait for all threads to complete
        for future in futures:
            future.result()

        # then release
        release_db_connection(storage_conn, storage_cur)
        release_db_connection(features_conn, features_cur)
        release_db_connection(ports_conn, ports_cur)
        release_db_connection(screens_conn, screens_cur)

    # postgresql does not have autocommit as standard so i need to manually commi
    json_conn.commit()
    return models

def get_model_id(laptop_name):
    model_id_conn, model_id_cur = get_db_connection()
    model = (laptop_name, )
    try:
        logger.info(f"Looking up model_id for laptop_name: '{laptop_name}'")
        stmnt = "SELECT * FROM laptop_models WHERE model_name = %s"
        model_id_cur.execute(stmnt, model)
        logger.info(f"Row count: {model_id_cur.rowcount}")

        if model_id_cur.rowcount > 1:
            logger.warning("More than one model found for this name.")
            return False
        elif model_id_cur.rowcount == 0:
            logger.info("No matching model found; will need to insert.")
            return False

        result = model_id_cur.fetchone()
        if result:
            model_id = result[0]
            logger.info(f"Found model_id: {model_id}")
            return model_id
        else:
            logger.warning("fetchone() returned None")
            return False

    except Exception as e:
        logger.error(f"Exception in get_model_id(): {e}")
        return False
    finally:
        release_db_connection(model_id_conn, model_id_cur)


def update_changes (json_diff_data, changes_conn):
        json_diff_added = json_diff_data.get('iterable_item_added')
        json_diff_removed = json_diff_data.get('iterable_item_removed')

        if json_diff_added:
            process_json_diff(json_diff_added, "added", changes_conn)
        elif json_diff_removed:
            process_json_diff(json_diff_removed, "removed", changes_conn)

def main():
    json_diff = None
    latest_json_archive = get_old_path()
    if latest_json_archive:
        logger.info(f"found old scrape {latest_json_archive}")
        try:
            json_diff = compare_new_and_old(latest_json_archive)
        except UnboundLocalError as e:
            logger.error(f"could not find an old path for the json data ERROR: {e}")
    update_changes(json_diff, conn)

if __name__ == "__main__":
    init_db_pool()  # Initialize the pool first
    # Now you can safely use get_db_connection()
    conn, cur = get_db_connection()
    main()