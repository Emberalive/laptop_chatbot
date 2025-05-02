import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from DBAccess.dbAccess import get_db_connection, release_db_connection
from loguru import logger

# Global database connection variables
global global_db_connection
global global_db_cursor

# Initialize lists to store different laptop details
product_details_list = []
screen_details_list = []
port_details_list = []
spec_details_list = []
feature_details_list = []
price_details_list = []

cpu_records_to_insert = []
gpu_records_to_insert = []

# Initialize the logger
logger.add(sys.stdout, format="{time} {level} {message}")
logger.add("logs/server.log", rotation="60 MB", retention="35 days", compression="zip")
logger_server = logger.bind(user="server")

# Load the JSON data from the file
try:
    logger_server.info("Opening the JSON data")
    with open('/home/samuel/laptop_chat_bot/server_side/scrapers/scraped_data/scraped_data.json', 'r') as json_file:
        laptops_data = json.load(json_file)
except Exception as server_path_error:
    logger_server.error(f"Server path didn't work, trying desktop path: ERROR: {server_path_error}")
    try:
        with open(
                '/home/sammy/Documents/2_brighton/sem2/groupProject-laptopChatBox/laptop_chatbot/Sam/server_side/scrapers/scraped_data/scraped_data.json',
                'r') as json_file:
            laptops_data = json.load(json_file)
    except Exception as desktop_path_error:
        logger_server.error(f"Desktop path didn't work, trying laptop path: ERROR: {desktop_path_error}")
        try:
            with open(
                    '/home/samuel/Documents/2_Brighton/sem2/GroupProject/laptop_chatbot/Sam/server_side/scrapers/scraped_data/scraped_data.json',
                    'r') as json_file:
                laptops_data = json.load(json_file)
        except Exception as laptop_path_error:
            logger_server.error(f"Laptop path didn't work: ERROR: {laptop_path_error}")

# Process each laptop in the JSON data
logger_server.info("Sorting through the JSON object lists\n")
for laptop_data in laptops_data:
    laptop_tables = laptop_data.get('tables', [])

    # Initialize dictionaries for each category
    product_info = {}
    screen_info = {}
    port_info = {}
    spec_info = {}
    features_info = {}
    price_info = {}

    # Process each table in the laptop data
    for table_data in laptop_tables:
        table_title = table_data.get('title', '')
        table_content = table_data.get('data', {})

        if table_title == 'Product Details':
            product_info.update(table_content)
        elif table_title == 'Screen':
            screen_info.update(table_content)
        elif table_title == 'Ports':
            port_info.update(table_content)
        elif table_title == 'Specs':
            spec_info.update(table_content)

            processor_name = table_content.get("Processor Name", "")
            processor_brand = table_content.get("Processor Brand", "")
            graphics_card = table_content.get("Graphics Card", "")

            if processor_brand and processor_name:
                cpu_records_to_insert.append((processor_brand, processor_name))

            if graphics_card:
                gpu_components = graphics_card.split(" ")
                gpu_brand = gpu_components[0] if gpu_components else "Unknown"
                gpu_model = " ".join(gpu_components[1:]) if len(gpu_components) > 1 else "Unknown"
                gpu_records_to_insert.append((gpu_brand, gpu_model))

        elif table_title == 'Features':
            features_info.update(table_content)
        elif table_title == 'Prices':
            price_info = table_content  # store the list directly

    # Append extracted details to their respective lists
    product_details_list.append(product_info)
    screen_details_list.append(screen_info)
    port_details_list.append(port_info)
    spec_details_list.append(spec_info)
    feature_details_list.append(features_info)
    price_details_list.append(price_info)

logger_server.info("Adding the dictionary items to their respective list objects\n")


def insert_cpu_records(cpu_records: list[tuple], db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into database table processors:")
        cpu_query = ("INSERT INTO processors (brand, model)"
                     "VALUES(%s, %s)"
                     "ON CONFLICT (model) DO NOTHING;")

        cursor.executemany(cpu_query, cpu_records)

        if cursor.rowcount > 0:
            logger_server.info(f"Inserted {len(cpu_records)} CPUs")

    except Exception as cpu_insert_error:
        logger_server.error(f"Failed to bulk insert CPUs: {cpu_insert_error}")
        raise
    finally:
        cursor.close()


def insert_gpu_records(gpu_records: list[tuple], db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into database table graphics_cards:")
        gpu_query = ("INSERT INTO graphics_cards (brand, model)"
                     "VALUES(%s, %s)"
                     "ON CONFLICT (model) DO NOTHING;")

        cursor.executemany(gpu_query, gpu_records)

        if cursor.rowcount > 0:
            logger_server.info(f"Inserted {len(gpu_records)} GPUs")

    except Exception as gpu_insert_error:
        logger_server.error(f"Failed to bulk insert GPUs: {gpu_insert_error}")
        raise
    finally:
        cursor.close()


def insert_laptop_model(brand_name, model_name, db_connection) -> int | None:
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into laptop_model")
        logger_server.info(f"Brand: {brand_name}, Model: {model_name}")
        laptop_model_query = (
            "INSERT INTO laptop_models (brand, model_name) "
            "VALUES(%s, %s) "
            "ON CONFLICT (model_name) "
            "DO UPDATE SET model_name = EXCLUDED.model_name "
            "RETURNING model_id"
        )
        laptop_model_values = (brand_name, model_name)
        cursor.execute(laptop_model_query, laptop_model_values)

        if cursor.rowcount > 0:
            logger_server.warning(f"Laptop model: {model_name} already exists in the database")
        else:
            logger_server.info(f"Laptop model: {model_name} was not in the database, has now been inserted")

        return cursor.fetchone()[0]

    except Exception as model_insert_error:
        logger_server.error(f"Error inserting into laptop model: {model_insert_error}")
        raise
    finally:
        cursor.close()


def insert_laptop_configuration(model_id, price, weight, battery_life, memory, os, cpu_model,
                                gpu_model, db_connection) -> int | None:
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into table laptop_configurations")
        logger_server.info(
            f"Price: {price}, Weight: {weight}, Battery Life: {battery_life}, "
            f"Memory: {memory}, OS: {os}, Processor: {cpu_model}, Graphics Card: {gpu_model}")

        config_query = (
            "INSERT INTO laptop_configurations (model_id, price, weight, battery_life, "
            "memory_installed, operating_system, processor, graphics_card)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            "RETURNING config_id")

        config_values = (
            model_id, price, weight, battery_life, memory, os, cpu_model, gpu_model)
        cursor.execute(config_query, config_values)

        return cursor.fetchone()[0]  # config_id

    except Exception as config_insert_error:
        logger_server.error(f"Error inserting laptop_configuration: {config_insert_error}")
        raise
    finally:
        cursor.close()


def insert_storage_configuration(config_id, storage_type, capacity, db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into database table configuration_storage")
        logger_server.info(f"Config ID: {config_id}, Storage Media: {storage_type}, Capacity: {capacity}")
        storage_query = ("INSERT INTO configuration_storage (config_id, storage_type, capacity)"
                         "VALUES(%s, %s, %s)")
        storage_values = (config_id, storage_type, capacity)
        cursor.execute(storage_query, storage_values)
    except Exception as storage_insert_error:
        logger_server.error(f"Error inserting storage configuration: {storage_insert_error}")
        raise
    finally:
        cursor.close()


def insert_laptop_features(config_id, has_backlit_keyboard, has_numeric_keypad,
                           has_bluetooth, db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into database table features")
        logger_server.info(
            f"Config ID: {config_id}, Backlit Keyboard: {has_backlit_keyboard}, "
            f"Num Pad: {has_numeric_keypad}, Bluetooth: {has_bluetooth}")

        features_query = ("INSERT INTO features (config_id, backlit_keyboard, numeric_keyboard, bluetooth)"
                          "VALUES(%s, %s, %s, %s)")
        features_values = (config_id, has_backlit_keyboard, has_numeric_keypad, has_bluetooth)
        cursor.execute(features_query, features_values)
    except Exception as features_insert_error:
        logger_server.error(f"Error inserting into features: {features_insert_error}")
        raise
    finally:
        cursor.close()


def insert_port_configuration(config_id, has_ethernet, has_hdmi, has_usb_c,
                              has_thunderbolt, has_display_port, db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into database table ports")
        logger_server.info(
            f"Config ID: {config_id} Ethernet: {has_ethernet}, HDMI: {has_hdmi}, "
            f"USB-C: {has_usb_c}, Thunderbolt: {has_thunderbolt}, Display Port: {has_display_port}")

        ports_query = ("INSERT INTO ports (config_id, ethernet, hdmi, usb_type_c, thunderbolt, display_port)"
                       "VALUES(%s, %s, %s, %s, %s, %s)")
        ports_values = (config_id, has_ethernet, has_hdmi, has_usb_c, has_thunderbolt, has_display_port)
        cursor.execute(ports_query, ports_values)
    except Exception as ports_insert_error:
        logger_server.error(f"Error with port configuration insertion: {ports_insert_error}")
        raise
    finally:
        cursor.close()


def insert_screen_configuration(config_id, size, resolution, is_touchscreen,
                                refresh_rate, db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into database table screens")
        logger_server.info(
            f"Config ID: {config_id}, Size: {size}, Resolution: {resolution}, "
            f"Touchscreen: {is_touchscreen}, Refresh Rate: {refresh_rate}")

        screen_query = ("INSERT INTO screens (config_id, size, resolution, touchscreen, refresh_rate)"
                        "VALUES(%s, %s, %s, %s, %s)")
        screen_values = (config_id, size, resolution, is_touchscreen, refresh_rate)
        cursor.execute(screen_query, screen_values)
    except Exception as screen_insert_error:
        logger_server.error(f"Error inserting screen configuration: {screen_insert_error}")
        raise
    finally:
        cursor.close()


try:
    global_db_connection, global_db_cursor = get_db_connection()
except Exception as db_connection_error:
    logger_server.error(f"Database connection error: {db_connection_error}")

# Process unique CPU and GPU records
unique_cpu_records = list(set(cpu_records_to_insert))
unique_gpu_records = list(set(gpu_records_to_insert))

insert_gpu_records(unique_gpu_records, global_db_connection)
insert_cpu_records(unique_cpu_records, global_db_connection)

# Process each laptop's data
for laptop_index in range(len(product_details_list)):
    current_product = product_details_list[laptop_index] if laptop_index < len(product_details_list) else {}
    current_screen = screen_details_list[laptop_index] if laptop_index < len(screen_details_list) else {}
    current_features = feature_details_list[laptop_index] if laptop_index < len(feature_details_list) else {}
    current_specs = spec_details_list[laptop_index] if laptop_index < len(spec_details_list) else {}
    current_prices = price_details_list[laptop_index] if laptop_index < len(price_details_list) else {}

    laptop_name = current_product.get('Name', '')
    laptop_weight = current_product.get('Weight', '')
    laptop_brand = current_product.get('Brand', '')
    laptop_battery = current_features.get('Battery Life', '')

    # Default price values
    laptop_price = "No Price available"
    price_shop = "No Shop available"

    if isinstance(current_prices, list) and current_prices:
        for price_entry in current_prices:
            entry_price = price_entry.get("price")
            entry_shop = price_entry.get("shop_url")
            if entry_price and entry_shop:
                laptop_price = entry_price
                price_shop = entry_shop
                break

    laptop_memory = current_specs.get('Memory Installed', '')
    laptop_os = current_features.get('Operating System', '') or "Not Specified"
    screen_size = current_screen.get('Size', '')

    cpu_brand = current_specs.get('Processor Brand', '').strip()
    cpu_model = current_specs.get("Processor Name", "").strip()

    if not cpu_brand or not cpu_model:
        logger_server.warning(f"Skipping laptop {laptop_name} - missing processor information")
        continue  # Skip this laptop entirely

    has_bluetooth = current_features.get("Bluetooth", False)
    has_numeric_keypad = current_features.get("Numeric Keyboard", False)
    has_backlit_keyboard = current_features.get("Backlit Keyboard", False)

    gpu_info = current_specs.get("Graphics Card", "")
    if not gpu_info:
        logger_server.info(f"Skipping GPU insertion for laptop: {laptop_name}, No GPU found")

    gpu_components = gpu_info.split(" ")
    gpu_brand = gpu_components[0] if gpu_components else "Unknown"
    gpu_model = " ".join(gpu_components[1:]) if len(gpu_components) > 1 else "Unknown"

    storage_info = current_specs.get("Storage", "").split()
    storage_capacity = storage_info[0] if storage_info else 'none'
    storage_type = storage_info[1].strip().upper() if len(storage_info) > 1 else 'none'

    has_ethernet = port_details_list[laptop_index].get("Ethernet (RJ45)", False)
    has_hdmi = port_details_list[laptop_index].get("HDMI", False)
    has_usb_c = port_details_list[laptop_index].get("USB Type-C", False)
    has_thunderbolt = port_details_list[laptop_index].get("Thunderbolt", False)
    has_display_port = port_details_list[laptop_index].get("Display Port", False)

    screen_resolution = screen_details_list[laptop_index].get("Resolution", "Unknown")
    screen_refresh_rate = screen_details_list[laptop_index].get("Refresh Rate", "Unknown")
    has_touchscreen = screen_details_list[laptop_index].get("Touchscreen", False)

    try:
        model_id = insert_laptop_model(laptop_brand, laptop_name, global_db_connection)

        if model_id is None:
            logger_server.error(f"Failed to insert laptop: {laptop_name}")
        else:
            logger_server.info(f"Inserted new laptop with ID: {model_id}")

        with ThreadPoolExecutor(max_workers=10) as executor:
            config_future = executor.submit(
                insert_laptop_configuration, model_id, laptop_price, laptop_weight,
                laptop_battery, laptop_memory, laptop_os, cpu_model, gpu_model,
                global_db_connection)

            try:
                config_id = config_future.result()
            except Exception as config_error:
                logger_server.error(f"Error inserting laptop configuration: {config_error}")
                config_id = None

            futures = [
                executor.submit(insert_port_configuration, config_id, has_ethernet,
                                has_hdmi, has_usb_c, has_thunderbolt, has_display_port,
                                global_db_connection),
                executor.submit(insert_laptop_features, config_id, has_backlit_keyboard,
                                has_numeric_keypad, has_bluetooth, global_db_connection),
                executor.submit(insert_screen_configuration, config_id, screen_size,
                                screen_resolution, has_touchscreen, screen_refresh_rate,
                                global_db_connection),
                executor.submit(insert_storage_configuration, config_id, storage_type,
                                storage_capacity, global_db_connection)
            ]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as worker_error:
                    logger_server.error(f"Error in worker: {worker_error}")

        global_db_connection.commit()
    except Exception as db_commit_error:
        global_db_connection.rollback()
        logger_server.error(
            f"Failed to insert laptop details (ports, features, screen, storage): {db_commit_error}")

release_db_connection(global_db_connection, global_db_connection)