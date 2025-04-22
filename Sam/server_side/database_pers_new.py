import json
from traceback import print_tb

# from distutils.util import execute
from DBAccess.dbAccess import db_access
import pprint

from database_persistence import features_values, ports_values, screen_values

# Initialize lists to store different laptop details
products = []
screens = []
ports = []
specs = []
features = []
prices = []

# Load the JSON data from the file
print("Opening the scraped data\n")
with open('/home/samuel/laptop_chat_bot/server_side/scrapers/scraped_data/scraped_data.json', 'r') as file:
    data = json.load(file)

# Loop through each laptop in the JSON data
print("Sorting through the JSON object lists\n")
for laptop in data:
    tables = laptop.get('tables', [])  # Extract tables from each laptop
    prices = laptop.get('Prices', [])

    # Initialize dictionaries for each category
    product_details = {}
    screen_details = {}
    port_details = {}
    spec_details = {}
    features_details = {}
    price_details = {}

    # loop through all the prices and add them to the dictionary
    for price in prices:
        price_details.update(price)

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
        elif title == 'Features':
            features_details.update(table_data)

    # Append extracted details to their respective lists
    products.append(product_details)
    screens.append(screen_details)
    ports.append(port_details)
    specs.append(spec_details)
    features.append(features_details)
    prices.append(price_details)

print("Adding the dictionary items to their respective list objects")

# Establish database connection
conn, cur = db_access()

print("\nClearing the database, so that new data can be inserted")
try:
    print("\nDeleting from features")
    delete_features = "DELETE FROM features;"
    cur.execute(delete_features)
    conn.commit()

    print("\nDeleting from gpu")
    delete_gpu = "DELETE FROM gpu;"
    cur.execute(delete_gpu)
    conn.commit()

    print("\nDeleting from storage")
    delete_storage = "DELETE FROM storage;"
    cur.execute(delete_storage)
    conn.commit()

    print("\nDeleting from ports")
    delete_ports = "DELETE FROM ports;"
    cur.execute(delete_ports)
    conn.commit()

    print("\nDeleting from screen")
    delete_screen = "DELETE FROM screen;"
    cur.execute(delete_screen)
    conn.commit()

    print("\nDelete from cpu")
    delete_cpu = "DELETE FROM cpu;"
    cur.execute(delete_cpu)
    conn.commit()

    print("\nDeleting from laptops")
    delete_laptops = "DELETE FROM laptops"
    cur.execute(delete_laptops)
    conn.commit()

except Exception as e:
    print(f"Database error: {e}")
    conn.rollback()

for i in range(len(products)):
    brand = products[i] if i < len(products) else {}
    screen = screens[i] if i < len(screens) else {}
    feature = features[i] if i < len(features) else {}
    spec = specs[i] if i < len(specs) else {}
    price_shop = prices[i] if i < len(prices) else {}
    laptop_price = prices[i] if i < len(prices) else {}

    laptop_name = brand.get('Name', '')
    weight = brand.get('Weight', '')
    laptop_brand = brand.get('Brand', '')
    battery_life = feature.get('Battery Life', '')

    # price = 1200
    price = laptop_price.get('price', '')
    if price == '':
        price = 'No Price available'

    if not battery_life:
        battery_life = "Not Specified"

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

    bluetooth = feature.get("Bluetooth", "")
    num_pad = features[i].get("Numeric Keyboard", "")
    backlit = features[i].get("Backlit Keyboard", "")

    gpu = spec.get("Graphics Card", "")

    if not gpu:
        print(f"Skipping GPU insertion for laptop: {laptop}, No GPU found")

    gpu_list = gpu.split(' ')
    gpu_brand = gpu_list[0] if gpu_list else "Unknown"
    gpu = gpu if gpu.lower() != "unknown" else "None"

    storage = spec.get("Storage", "")

    storage_list = storage.split()

    if not storage_list:
        amount = 'none'
        storage_type = 'none'
    else:
        amount = storage_list[0]
        storage_type = storage_list[1].strip().upper()

    # storage = spec.get("Storage", "")
    # storage_list = storage.split(" ")
    # amount = storage_list[0]
    # storage_type = storage_list[1]

    ethernet = ports[i].get("Ethernet (RJ45)", "None")
    hdmi = ports[i].get("HDMI", "None")
    usb_c = ports[i].get("USB Type-C", "None")
    thunderbolt = ports[i].get("Thunderbolt", "None")
    display_port = ports[i].get("Display Port", "None")

    screen_res = screens[i].get("Resolution", "Unknown")
    refresh_rate = screens[i].get("Refresh Rate", "Unknown")
    touch_screen = screens[i].get("Touchscreen", "Unknown")


    #Inserting the processor table
    try:
        cpu_querey = ("INSERT INTO processors (brand, model)"
                      "VALUES(%s, %s)")
        cpu_values = (cpu_brand, cpu_name)
        conn.execute(cpu_querey, cpu_values)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("There was an error")
    finally:
        conn.close()

    #Inerting into the table gpu
    try:
        gpu_query = ("INSERT INTO graphics_cards (brand, model"
                     "VALUES(%s, %s)")
        gpu_values = (gpu_brand, gpu)
        conn.execute(gpu_query, gpu_values)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"There was an error: {e}")
    finally:
        conn.close()

    #Inserting into the laptop model and laptop configurations
    try:
        laptop_querey = "SELECT * FROM laptop_models WHERE model_name = %s"
        laptop_Values = (laptop_name)
        print(f"Inserting into laptop_models")

        results = cur.fetchall()

        if results == 0:
            laptop_model_query = ("INSERT INTO laptop_models (brand, model_name)"
                                  "VALUES (%s, %s)")
            laptop_model_values = (brand, laptop_name)



        if results == 1:
            for row in results:
                model_id = row[0]

            laptop_configuration_query = ("INSERT INTO laptop_configurations (model_id, price, weight, battery_life, memory_installed, operating_system, processor, graphics_card)"
                                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                                          "RETURNING config_id")
            laptop_configuration_values = (model_id, price, weight, battery_life, memory_installed, operating_system, cpu_name, gpu)
            cur.execute(laptop_configuration_query, laptop_configuration_values)
            config_id = cur.fetchone()[0]
            conn.commit()
        else:
            print("there is more than one laptop_model, error")

    except Exception as e:
        print(f"error lol: {e}")

    #Inserting into the storage tables
    try:
        config_id_query = "SELECT type FROM storge_types WHERE type = %s", (storage_type)
        if cur.fetchone() is None:
            print(f"Storage type '{storage_type}' not found. Skipping insert.")
        else:
            configuration_storage_querey = ("INSERT INTO configuration_storage (config_id, storage_type, capacity)"
                                        "VALUES(%s, %s, %s")
        configuration_storage_values = (config_id, storage_type, amount)
        conn.execute(configuration_storage_querey, configuration_storage_values)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"error and that: {e}")
    finally:
        conn.close()


    #Inserting into the features table
    try:
        features_querey = ("INSERT INTO features (config_id, backlit_keyboard, numeric_keyboard, bluetooth)"
                           "VALUES(%s, %s, %s, %s")
        features_values = (config_id, backlit, num_pad, bluetooth)
        conn.execut(features_querey, features_values)
        conn.commit()
    except EXception as e:
        conn.rollback()
        print(f"error with the insert statement: {e}")
    finally:
        conn.close()


    #Inserting into the ports table
    try:
        ports_querey = ("INSERT INTO ports (config_id, ethernet, hdmi, usb_type_c, thunderbolt, display_port"
                        "VALUES(%s, %s, %s, %s, %s, %s")
        ports_values = (config_id, ethernet, hdmi, usb_c, thunderbolt, display_port)
        conn.execute(ports_querey, ports_values)
        conn.commit()
    except EXception as e:
        conn.rollback()
        print(f"error with the database and that: {e}")
    finally:
        conn.close()

    try:
        screens_querey = ("INSERT INTO screens (config_id, size, resolution, touchscreen, refresh_rate"
                          "VALUES(%s, %s, %s, %s, %s, %s)")
        screen_values = (config_id, screen_size, touch_screen, screen_res, refresh_rate)
        conn.execute(screens_querey, screen_values)
        conn.commit()
    except EXception as e:
        conn.rollback()
        print(f"error and that i guess: {e}")
    finally:
        conn.close()































