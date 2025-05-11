import re
from deepdiff import DeepDiff
import json
import pprint
import sys
import os
from loguru import logger
from datetime import datetime
from DBAccess.dbAccess import get_db_connection, release_db_connection, init_db_pool
from DBAccess.database_persistence_V3 import insert_configuration, insert_laptop_model,  insert_gpu_records, insert_cpu_records,  bulk_insert_storage, bulk_insert_features,  bulk_insert_ports, bulk_insert_screens


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
            logger.info(pprint.pprint(diff))
            return diff
        else:
            logger.info("No differences found between the two files.")
            return None

    except Exception as e:
        logger.error(f"error in attempting to compare the old and new json data {e}")


def process_json_diff(diff_dict, action):
    models = []

    laptop_model_records = []
    feature_records = []
    ports_records = []
    storage_records = []
    screen_records = []

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
        laptop_model = weight = cpu = gpu = memory = o_s = battery_life = "N/A"

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
                    storage_type = storage_info[1]


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
                    display_port = table.get('Display Port', False)
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
                    laptop_price = table_data[0].get('price')
                    laptop_shop_url = table_data[0].get('shop_url')




                model_id = get_model_id(laptop_model)

                if not model_id:
                    laptop_model_records.append((laptop_brand, laptop_model, laptop_image))
                    insert_laptop_model(laptop_model_records, conn)

                config_id = insert_configuration(model_id)
                storage_records.append((config_id, storage_type))
                feature_records.append((config_id, back_lit, num_pad, bluetooth))
                ports_records.append((config_id, ethernet, hdmi, usb_type_c, thunderbolt, display_port))
                screen_records.append((config_id, size, resolution, touch_screen, refresh_rate))



            # Only log after processing all tables
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
        else:
            logger.warning(f"No valid tables found for {root_key}")

    if models:
        logger.info(f"Laptop model(s) to {action}: {models}")
    else:
        logger.warning(f"No laptop models found in {action} items")

    bulk_insert_storage(storage_records, conn)
    bulk_insert_features(feature_records, conn)
    bulk_insert_ports(ports_records, conn)
    bulk_insert_screens(screen_records, conn)


    return models

def get_model_id(laptop_name):
    conn, cur = get_db_connection()
    model = (laptop_name, )
    try:
        stmnt = ("SELECT * FROM laptop_models WHERE model_name = %s")

        cur.execute(stmnt, model)
        row_count = cur.rowcount
        if row_count > 1:
            logger.info(f"there is more than one laptop_model, error!!!!!!!")
            return False
        elif row_count == 0:
            logger.info(f"Need to insert the laptop model")
            return False
        model_id = cur.fetchone()[0]
        return model_id
    except Exception as e:
        logger.error(f"error getting the model_id for the laptop ERROR {e}")

        return None
    finally:
        release_db_connection(conn, cur)



def update_changes (json_diff_data):
        json_diff_added = json_diff_data.get('iterable_item_added')
        json_diff_removed = json_diff_data.get('iterable_item_removed')

        if json_diff_added:
            process_json_diff(json_diff_added, "added")
        elif json_diff_removed:
            process_json_diff(json_diff_removed, "removed")

def main():

    latest_json_archive = get_old_path()
    if latest_json_archive:
        logger.info(f"found old scrape {latest_json_archive}")
        try:
            json_diff = compare_new_and_old(latest_json_archive)
        except UnboundLocalError as e:
            logger.error(f"could not find an old path for the json data ERROR: {e}")
    update_changes(json_diff)

if __name__ == "__main__":
    init_db_pool()  # Initialize the pool first
    # Now you can safely use get_db_connection()
    conn, cur = get_db_connection()
    main()