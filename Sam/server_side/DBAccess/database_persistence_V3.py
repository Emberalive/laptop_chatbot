import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dbAccess import get_db_connection, release_db_connection, init_db_pool
from loguru import logger

#this version takes a whopping 14:49:77
# with new improvements it is now 7:15
# latest speed is 6:10
#newest speed 5:28
#many pool executors = 5:23:21
#execute many for gpu and cpu 4:38:06
#newest speed 3:45:03

# function to bulk insert the cpu records
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
        db_connection.rollback()
        logger_server.error(f"Failed to bulk insert CPUs: {cpu_insert_error}")
        raise
    finally:
        cursor.close()

# function to bulk insert the cpu records
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
        db_connection.rollback()
        logger_server.error(f"Failed to bulk insert GPUs: {gpu_insert_error}")
        raise
    finally:
        cursor.close()

# function to insert all the laptop models and get their return value
def insert_laptop_model(model_records: list[tuple], db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into laptop_model")
        laptop_model_query = (
            "INSERT INTO laptop_models (brand, model_name) "
            "VALUES(%s, %s) "
            "ON CONFLICT (model_name) "
            "DO UPDATE SET model_name = EXCLUDED.model_name "
            "RETURNING model_id, model_name"
        )
        results = {}
        for record in model_records:
            cursor.execute(laptop_model_query, record)
            model_id, model_name = cursor.fetchone()
            results[model_name] = model_id
        logger.info(f"inserted {len(results)} laptop models")
        return results
    except Exception as model_insert_error:
        db_connection.rollback()
        logger.error(f"Bulk model insertion failed: {model_insert_error}")
        raise
    finally:
        cursor.close()

# function to insert all the laptop configurations, individually as i need a return value, which i cant get with execute many
def insert_configuration(model_id, price, weight, battery_life, memory_installed, os, processor, gpu, db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info(f"model ID: {model_id}, Weight: {weight}, Price: {price}, Battery Life: {battery_life}, Memory: {memory_installed}, Operating Sys: {os}, GPU: {gpu}, CPU: {processor}")
        logger_server.info("\nInserting into table laptop_configurations")
        config_query = (
            "INSERT INTO laptop_configurations (model_id, price, weight, battery_life, "
            "memory_installed, operating_system, processor, graphics_card)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            "RETURNING config_id")
        config_values = (model_id, price, weight, battery_life, memory_installed, os, processor, gpu)
        cursor.execute(config_query, config_values)

        return cursor.fetchone()[0]
    except Exception as config_insert_error:
        db_connection.rollback()
        logger_server.error(f"Error inserting laptop_configuration: {config_insert_error}")
        raise
    finally:
        cursor.close()

# function to bulk insert the storage records
def bulk_insert_storage(storage_records: list[tuple], db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into database table configuration_storage")
        storage_query = ("INSERT INTO configuration_storage (config_id, storage_type, capacity)"
                         "VALUES(%s, %s, %s)")
        cursor.executemany(storage_query, storage_records)
        logger_server.info(f"inserted storages: {len(storage_records)}")
    except Exception as storage_insert_error:
        db_connection.rollback()
        logger_server.error(f"Error inserting storage configuration: {storage_insert_error}")
        raise
    finally:
        cursor.close()

# function to bulk insert the feature records
def bulk_insert_features(features_records: list[tuple], db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into database table features")
        features_query = ("INSERT INTO features (config_id, backlit_keyboard, numeric_keyboard, bluetooth)"
                          "VALUES(%s, %s, %s, %s)")
        cursor.executemany(features_query, features_records)
        logger_server.info(f"inserted storages: {len(features_records)}")
    except Exception as features_insert_error:
        db_connection.rollback()
        logger_server.error(f"Error inserting into features: {features_insert_error}")
        raise
    finally:
        cursor.close()

# function to bulk insert the ports records
def bulk_insert_ports(ports_records: list[tuple], db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into database table ports")
        ports_query = ("INSERT INTO ports (config_id, ethernet, hdmi, usb_type_c, thunderbolt, display_port)"
                       "VALUES(%s, %s, %s, %s, %s, %s)")
        cursor.executemany(ports_query, ports_records)
        logger_server.info(f"inserted storages: {len(ports_records)}")
    except Exception as ports_insert_error:
        db_connection.rollback()
        logger_server.error(f"Error with port configuration insertion: {ports_insert_error}")
        raise
    finally:
        cursor.close()

# function to bulk insert the screen records
def bulk_insert_screens(screens_records: list[tuple], db_connection):
    cursor = db_connection.cursor()
    try:
        logger_server.info("\nInserting into database table screens")
        screen_query = ("INSERT INTO screens (config_id, size, resolution, touchscreen, refresh_rate)"
                        "VALUES(%s, %s, %s, %s, %s)")
        cursor.executemany(screen_query, screens_records)
        logger_server.info(f"inserted storages: {len(screens_records)}")
    except Exception as screen_insert_error:
        db_connection.rollback()
        logger_server.error(f"Error inserting screen configuration: {screen_insert_error}")
        raise
    finally:
        cursor.close()

def main():
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

    # Load the JSON data from the file
    try:
        #try with the server path
        logger_server.info("Opening the JSON data")
        with open('/home/samuel/laptop_chatbot/Sam/server_side/scrapers/scraped_data/latest.json', 'r') as json_file:
            laptops_data = json.load(json_file)
    except Exception as server_path_error:
        logger_server.error(f"Server path didn't work, trying desktop path: ERROR: {server_path_error}")
        try:
            #try with the desktop path
            with open(
                    '/home/sammy/Documents/2_brighton/sem2/groupProject-laptopChatBox/laptop_chatbot/Sam/server_side/scrapers/scraped_data/latest.json',
                    'r') as json_file:
                laptops_data = json.load(json_file)
        except Exception as desktop_path_error:
            logger_server.error(f"Desktop path didn't work, trying laptop path: ERROR: {desktop_path_error}")
            try:
                #try with the laptop path
                with open(
                        '/scrapers/scraped_data/latest.json',
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

        # storing all the json objects in the dictionaries
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

                # grabbing all the gpu, and cpu data and putting them in their own list
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

        logger_server.info("Adding the dictionary items to their respective list objects\n")

        # Append extracted details to their respective lists, so i can iterate through index
        product_details_list.append(product_info)
        screen_details_list.append(screen_info)
        port_details_list.append(port_info)
        spec_details_list.append(spec_info)
        feature_details_list.append(features_info)
        price_details_list.append(price_info)

    # getting all the laptop model's and putting them in a unique list
    unique_laptop_models = set()
    for product in product_details_list:
        brand = product.get('Brand', '').strip()
        name = product.get('Name', '').strip()
        if brand and name:
            unique_laptop_models.add((brand, name))
    #asigning the unique list to a list of tuples
    laptop_model_records = list(unique_laptop_models)
    # #Notes


    # #I can put all the insert data into a list and use the .executemany() function instead of doing them all separate: DONE
    # #I could also add more workers to each worker pool while there is a wait for database read and write: DONE
    # #Also I could reduce my prints as each print has a very small hang as the print to console is happening DONE
    # #pass create mny own cursor per method as cursors are not thread safe: DONE
    # #make it so their is a dictionary that holds the laptop_model and its corresponding id, so that I
    # can insert them in bulk, and use the dictionary so that I can grab the id and insert it into the laptop configuration table

    # attempt to take a connection from the connection pool
    try:
        global_db_connection, global_db_cursor = get_db_connection()
    except Exception as db_connection_error:
        logger_server.error(f"Database connection error: {db_connection_error}")

    # making the cpu, and gpu records unique
    unique_cpu_records = list(set(cpu_records_to_insert))
    unique_gpu_records = list(set(gpu_records_to_insert))

    insert_gpu_records(unique_gpu_records, global_db_connection)
    insert_cpu_records(unique_cpu_records, global_db_connection)

    #getting the laptop_model dictionary, doesn't need to be set as it is done through the bulk insert, based on database restrictions
    model_lookup = insert_laptop_model(laptop_model_records, global_db_connection)


    # Lists to hold all prepared data for bulk insertion
    storages = []
    features = []
    ports = []
    screens = []

    # Process each laptop's data
    for laptop_index in range(len(product_details_list)):
        # initialise data access point for each laptop's data
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

        # get the model_id based on the model_lookup returned by the model insert function
        model_name = current_product.get('Name', '').strip()
        model_id = model_lookup.get(model_name)

        if not model_id:
            continue  # Skip if model not found

        # insert the configuration for the current laptop, and assign the return value to a variable
        config_id = insert_configuration(model_id, laptop_price, laptop_weight, laptop_battery, laptop_memory, laptop_os, cpu_model, gpu_model, global_db_connection)

        # Prepare table bulk inserts with the current laptops config_id initialized above
        storages.append((config_id, storage_type, storage_capacity))
        features.append((config_id, has_backlit_keyboard, has_numeric_keypad, has_bluetooth))
        ports.append((config_id, has_ethernet, has_hdmi, has_usb_c, has_thunderbolt, has_display_port))
        screens.append((config_id, screen_size, screen_resolution, has_touchscreen, screen_refresh_rate))

        # Bulk insert all related data parallelized
    try:
        with ThreadPoolExecutor(max_workers=11) as executor:
            futures = [
                bulk_insert_storage(storages, global_db_connection),
                bulk_insert_features(features, global_db_connection),
                bulk_insert_ports(ports, global_db_connection),
                bulk_insert_screens(screens, global_db_connection)
            ]
    except Exception as worker_error:
        logger.error(f"Error with one of the workers ERROR:{worker_error}")
    global_db_connection.commit()

    # return the database connection to the pool
    release_db_connection(global_db_connection, global_db_connection)

if __name__ == "main":
    # Initialize the logger
    logger.remove()
    logger.add(sys.stdout, format="{time} {level} {message}")
    logger.add("../logs/server.log", rotation="60 MB", retention="35 days", compression="zip")
    logger_server = logger.bind(user="server")

    init_db_pool()
    main()

