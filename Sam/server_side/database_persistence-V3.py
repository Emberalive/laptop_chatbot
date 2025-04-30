import json

#this version takes a whopping 14:49:77
# with new improvements it is now 7:15
# latest speed is 6:10
#newest speed 5:28
#many pool executors = 5:23:21
#execute many for gpu and cpu 4:38:06

from concurrent.futures import ThreadPoolExecutor, as_completed
from os.path import split

from DBAccess.dbAccess import get_db_connection
from DBAccess.dbAccess import release_db_connection

# Initialize lists to store different laptop details
products = []
screens = []
ports = []
specs = []
features = []
prices = []

insert_cpu_data = []
insert_gpu_data = []


# Load the JSON data from the file
try:
    #server path
    print("Opening the scraped data\n")
    with open('/home/samuel/laptop_chat_bot/server_side/scrapers/scraped_data/scraped_data.json', 'r') as file:
        data = json.load(file)
except Exception as e:
    print(f"server path didn't work, trying desktop path ERROR: {e}")
    try:
        # desktop path
        with open('/home/sammy/Documents/2_brighton/sem2/groupProject-laptopChatBox/laptop_chatbot/Sam/server_side/scrapers/scraped_data/scraped_data.json', 'r') as file:
            data = json.load(file)
    except Exception as e:
        print(f"desktop path didnt work, trying laptop path ERROR: {e}")
        #laptop path
        with open('/home/samuel/Documents/2_Brighton/sem2/GroupProject/laptop_chatbot/Sam/server_side/scrapers/scraped_data/scraped_data.json', 'r') as file:
            data = json.load(file)


# Loop through each laptop in the JSON data
print("Sorting through the JSON object lists\n")
for laptop in data:
    tables = laptop.get('tables', [])  # Extract tables from each laptop

    # Initialize dictionaries for each category
    product_details = {}
    screen_details = {}
    port_details = {}
    spec_details = {}
    features_details = {}
    price_details = {}

    # Loop through each table and store data in respective dictionaries
    for table in tables:
        title = table.get('title', '')
        table_data = table.get('data', {})

        if title == 'Product Details':
            product_details.update(table_data)
        elif title == 'Screen':
            screen_details.update(table_data)
        elif title == 'Ports':
            port_details.update(table_data)
        elif title == 'Specs':
            spec_details.update(table_data)

            cpu_name = table_data.get("Processor Name", "")
            cpu_brand = table_data.get("Processor Brand", "")
            gpu_data = table_data.get("Graphics Card", "")


            if cpu_brand and cpu_name:
               insert_cpu_data.append((cpu_brand, cpu_name))

            if gpu_data:
                gpu_list = gpu_data.split(" ")
                gpu_brand = gpu_list[0] if gpu_list else "Unknown"
                gpu_name = " ".join(gpu_list[1:]) if len(gpu_list) > 1 else "Unknown"
                insert_gpu_data.append((gpu_brand, gpu_name))

        elif title == 'Features':
            features_details.update(table_data)
        elif title == 'Prices':
            price_details = table_data  # store the list directly

    # Append extracted details to their respective lists
    products.append(product_details)
    screens.append(screen_details)
    ports.append(port_details)
    specs.append(spec_details)
    features.append(features_details)
    prices.append(price_details)



print("Adding the dictionary items to their respective list objects")

def insert_cpu (cpu_data: list[tuple], conn):
    cur = conn.cursor()
    try:
        print("\nInserting into database table processors:")
        cpu_querey = ("INSERT INTO processors (brand, model)"
                      "VALUES(%s, %s)"
                      "ON CONFLICT (model) DO NOTHING;")

        cur.executemany(cpu_querey, cpu_data)

        if cur.rowcount > 0:
            print(f"Inserted {len(cpu_data)} CPUs")

    except Exception as e:
        print(f"Failed to bulk insert CPUs: {e}")
        raise #this reRaises the error to be caught by the global error handler
    finally:
        cur.close()

def insert_gpu (gpu_data: list[tuple], conn):
    try:
        cur = conn.cursor()
        print("\nInserting into database table graphics_cards:")
        gpu_query = ("INSERT INTO graphics_cards (brand, model)"
                     "VALUES(%s, %s)"
                     "ON CONFLICT (model) DO NOTHING;")

        cur.executemany(gpu_query, gpu_data)

        if cur.rowcount > 0:
            print(f"Inserted {len(gpu_data)} CPUs")

    except Exception as e:
        print(f"Failed to bulk insert GPUs: {e}")
        raise #this reRaises the error to be caught by the global error handler
    finally:
        cur.close()

def insert_laptop_model(brand, model, conn)-> int| None:
    try:
        cur = conn.cursor()
        print("\nInserting into laptop_model")
        print(f"Brand: {brand}, Model: {model}")
        laptop_model_query = (
            "INSERT INTO laptop_models (brand, model_name) "
            "VALUES(%s, %s) "
            "ON CONFLICT (model_name) "
            "DO UPDATE SET model_name = EXCLUDED.model_name " #this updates the row that has the model name in,to the same value, allowing me to return model_id
            "RETURNING model_id"
        )
        laptop_model_values = (brand, model)
        cur.execute(laptop_model_query, laptop_model_values)

        if cur.rowcount > 0:
            print(f"laptop model: {model} already exists in the database")
        else:
            print(f"laptop model: {model} was not in the database, has now been inserted")

        return cur.fetchone()[0]

    except Exception as e:
        print(f"Error inserting into laptop model: {e}")
        raise
    finally:
        cur.close()

def insert_laptop_configuration(model_id, laptop_price, laptop_weight, laptop_battery_life, laptop_memory, os, cpu,
                                gpu_name, conn)-> int| None:
    try:
        cur = conn.cursor()
        print("\nInserting into table laptop_configurations")
        print(
            f"Price: {laptop_price}, Weight: {laptop_weight}, Battery Life: {laptop_battery_life}, Memory: {laptop_memory}, OS: {os}, Processor: {cpu}, Graphics Card: {gpu_name}")
        laptop_configuration_query = (
            "INSERT INTO laptop_configurations (model_id, price, weight, battery_life, memory_installed, operating_system, processor, graphics_card)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            "RETURNING config_id")
        laptop_configuration_values = (
        model_id, laptop_price, laptop_weight, laptop_battery_life, laptop_memory, os, cpu, gpu_name)
        cur.execute(laptop_configuration_query, laptop_configuration_values)

        return cur.fetchone()[0]  # config_id

    except Exception as e:
        print(f"Error inserting laptop_configuration: {e}")
        raise
    finally:
        cur.close()


def insert_storage(config_id, storagetype, capacity, conn):
    try:
        cur = conn.cursor()
        print("\nInserting into database table configuration_storage")
        print(f"Config ID: {config_id}, Storage Media: {storagetype}, Capacity: {capacity}")
        configuration_storage_querey = ("INSERT INTO configuration_storage (config_id, storage_type, capacity)"
                                        "VALUES(%s, %s, %s)")
        configuration_storage_values = (config_id, storagetype, capacity)
        cur.execute(configuration_storage_querey, configuration_storage_values)
    except Exception as e:
        print(f"Error inserting storage configuration: {e}")
        raise #this reRaises the error to be caught by the global error handler
    finally:
        cur.close()

def insert_features(config_id, backlit_keyb, number_pad, blue_tooth, conn):
    try:
        cur = conn.cursor()
        print("\nInserting into database table features")
        print(f"Config ID: {config_id}, Backlit Keyboard: {backlit_keyb}, Num Pad: {number_pad}, Bluetooth: {blue_tooth}")
        features_querey = ("INSERT INTO features (config_id, backlit_keyboard, numeric_keyboard, bluetooth)"
                           "VALUES(%s, %s, %s, %s)")
        features_values = (config_id, backlit_keyb, number_pad, blue_tooth)
        cur.execute(features_querey, features_values)
    except Exception as e:
        print(f"error inserting into features: {e}")
        raise #this reRaises the error to be caught by the global error handler
    finally:
        cur.close()

def insert_ports(config_id, eth, hdmi_port, usb_type_c, thunder, d_p, conn):
    try:
        cur = conn.cursor()
        print("\nInserting into database table ports")
        print(f"Config ID: {config_id} Ethernet: {eth}, HDMI: {hdmi_port}, USB - C: {usb_type_c}, Thunderbolt: {thunder}, Display Port: {d_p}")
        ports_querey = ("INSERT INTO ports (config_id, ethernet, hdmi, usb_type_c, thunderbolt, display_port)"
                        "VALUES(%s, %s, %s, %s, %s, %s)")
        ports_values = (config_id, eth, hdmi_port, usb_type_c, thunder, d_p)
        cur.execute(ports_querey, ports_values)
    except Exception as e:
        print(f"error with the database and that: {e}")
        raise #this reRaises the error to be caught by the global error handler
    cur.close()

def insert_screens(config_id, size, resolution, touch, ref_rate, conn):
    try:
        cur = conn.cursor()
        print("\nInserting into database table screens")
        print(f"Config ID: {config_id}, Size: {size}, Resolution: {resolution}, Touchscreen: {touch}, Refresh Rate: {ref_rate}")
        screens_querey = ("INSERT INTO screens (config_id, size, resolution, touchscreen, refresh_rate)"
                          "VALUES(%s, %s, %s, %s, %s)")
        screen_values = (config_id, size, resolution, touch, ref_rate)
        cur.execute(screens_querey, screen_values)
    except Exception as e:
        print(f"error and that i guess: {e}")
        raise #this reRaises the error to be caught by the global error handler
    finally:
        cur.close()


try:
    conn, cur = get_db_connection()
except Exception as e:
    print(f"We had an error connecting to the database ERROR: {e}")

#Notes
#I can put all the insert data into a list and use the .executemany() function instead of doing them all separate
#I could also add more workers to each worker pool while there is a wait for database read and write: DONE
#Also I could reduce my prints as each print has a very small hang as the print to console is happening
#pass create mny own cursor per method as cursors are not thread safe: DONE


insert_cpu_list = list(set(insert_cpu_data))
insert_gpu_list = list(set(insert_gpu_data))

try:
    insert_gpu(insert_gpu_list, conn)
except Exception as e:
    print(f"error inserting gpu's in bulk: {e}")
try:
    insert_cpu(insert_cpu_list, conn)
except Exception as e:
    print(f"Error inserting gpu's in bulk: {e}")
for i in range(len(products)):
    counter = 0
    brand = products[i] if i < len(products) else {}
    screen = screens[i] if i < len(screens) else {}
    feature = features[i] if i < len(features) else {}
    spec = specs[i] if i < len(specs) else {}
    laptop_price = prices[i] if i < len(prices) else {}

    laptop_name = brand.get('Name', '')
    weight = brand.get('Weight', '')
    laptop_brand = brand.get('Brand', '')
    battery_life = feature.get('Battery Life', '')

    price = 1200

    laptop_shops = []
    laptop_prices = []
    for details in laptop_price:
        if not laptop_price:
            shop = 'No Shop available'
            Price = 'No Price available'

            laptop_prices.append(Price)
            laptop_shops.append(Shop)
        else:
            Price = details.get('price', 'No Price available')
            Shop = details.get('shop_url', 'No Shop available')

            laptop_prices.append(Price)
            laptop_shops.append(Shop)

    print(laptop_shops)
    print(laptop_prices)


    memory_installed = spec.get('Memory Installed', '')
    operating_system = feature.get('Operating System', '')

    if not operating_system:
        operating_system = "Not Specified"

    screen_size = screen.get('Size', '')

    # first_price_shop = price_shop[0] if price_shop else {'shop_url': 'no url', 'price': 'no price'}

    # shop = first_price_shop.get('shop_url', '')
    # price = price_shop.get('price', '')

    # print("\nPrice: " + price + " , " + shop)

    cpu_brand = spec.get('Processor Brand', '')
    cpu_name = spec.get("Processor Name", "")

    bluetooth = feature.get("Bluetooth", False)
    num_pad = features[i].get("Numeric Keyboard", False)
    backlit = features[i].get("Backlit Keyboard", False)

    gpu = spec.get("Graphics Card", "")

    if not gpu:
        print(f"Skipping GPU insertion for laptop: {laptop_name}, No GPU found")

    gpu_list = gpu.split(" ")
    gpu_brand = gpu_list[0] if gpu_list else "Unknown"
    gpu_name = " ".join(gpu_list[1:]) if len(gpu_list) > 1 else "Unknown"

    storage = spec.get("Storage", "")

    storage_list = storage.split()

    if not storage_list:
        amount = 'none'
        storage_type = 'none'
    else:
        amount = storage_list[0]
        storage_type = storage_list[1].strip().upper()

    ethernet = ports[i].get("Ethernet (RJ45)", False)
    hdmi = ports[i].get("HDMI", False)
    usb_c = ports[i].get("USB Type-C", False)
    thunderbolt = ports[i].get("Thunderbolt", False)
    display_port = ports[i].get("Display Port", False)

    screen_res = screens[i].get("Resolution", "Unknown")
    refresh_rate = screens[i].get("Refresh Rate", "Unknown")
    touch_screen = screens[i].get("Touchscreen", False)




    try:
        model_id = insert_laptop_model(laptop_brand, laptop_name, conn)

        if model_id is None:
            print(f"Failed to insert laptop: {laptop_name}")
        else:
            print(f"Inserted new laptop with ID: {model_id}")

        with ThreadPoolExecutor(max_workers=10) as executor:
            config_future = executor.submit(
                insert_laptop_configuration, model_id, price, weight, battery_life, memory_installed, operating_system, cpu_name, gpu_name, conn)

            try:
                config_id = config_future.result()
            except Exception as e:
                print(f"Error insetring laptop configuration, ERROR: {e}")
                config_id = None

            futures = [
            executor.submit(insert_ports, config_id, ethernet, hdmi, usb_c, thunderbolt, display_port, conn),
            executor.submit(insert_features, config_id, backlit, num_pad, bluetooth, conn),
            executor.submit(insert_screens, config_id, screen_size, screen_res, touch_screen, refresh_rate, conn),
            executor.submit(insert_storage, config_id, storage_type, amount, conn)
            ]
            for future in as_completed(futures):
                try:
                    future.result()  # Raises exceptions if any occurred
                except Exception as e:
                    print(f"Error in worker: {e}")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"failed to insert the details for the laptop could be 'ports, features, screen, storage' ERROR: {e}")

#bulk inserting into cpu and gpu
release_db_connection(conn, conn)