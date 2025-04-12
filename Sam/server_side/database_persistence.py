import json
from DBAccess.dbAccess import db_access
import pprint

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

    amount = storage_list[0] if storage_list else 'none'
    storage_type = storage_list[1] if len(storage_list) > 1 else 'none'

    ethernet = ports[i].get("Ethernet (RJ45)", "None")
    hdmi = ports[i].get("HDMI", "None")
    usb_c = ports[i].get("USB Type-C", "None")
    thunderbolt = ports[i].get("Thunderbolt", "None")
    display_port = ports[i].get("Display Port", "None")

    screen_res = screens[i].get("Resolution", "Unknown")
    refresh_rate = screens[i].get("Refresh Rate", "Unknown")
    touch_screen = screens[i].get("Touchscreen", "Unknown")

    try:
        print("\nInserting into database table laptops:")
        print(
            f"Name: {laptop_name}, Weight: {weight}, Battery Life: {battery_life}, Memory Installed: {memory_installed}, OS: {operating_system}, Screen Size: {screen_size}, Price: {price}")

        laptop_query = '''
            INSERT INTO laptops (model, brand, operating_system, screen_size, price, weight, battery_life, memory_installed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        laptop_values = (
        laptop_name, laptop_brand, operating_system, screen_size, price, weight, battery_life, memory_installed)

        cur.execute(laptop_query, laptop_values)
        conn.commit()

    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

    composite_keys = (screen_size, memory_installed, weight, laptop_name)

    try:
        print("\nInserting into database table features")
        print(f"Laptop: {laptop_name}, Bluetooth: {bluetooth}, Num Pad: {num_pad}, Backlit: {backlit}")

        features_query = '''
            INSERT INTO features (laptop_screen_size, laptop_memory, laptop_weight, laptop_model, bluetooth, num_pad, backlit_keyboard)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        '''
        features_values = (*composite_keys, bluetooth, num_pad, backlit)

        cur.execute(features_query, features_values)
        conn.commit()

    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

    try:
        print("\nInserting into database table gpu")
        print(f"Laptop: {laptop_name}, GPU: {gpu}, Brand: {gpu_brand}")

        gpu_query = '''
            INSERT INTO gpu (laptop_screen_size, laptop_memory, laptop_weight, laptop_model, model, brand)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        gpu_values = (*composite_keys, gpu, gpu_brand)

        cur.execute(gpu_query, gpu_values)
        conn.commit()

    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

    try:
        print("\nInserting into database table storage")
        print(f"laptop: {laptop_name}, Storage Amount: {amount}, Storage Type: {storage_type}")

        storage_query = '''
        INSERT INTO storage (laptop_screen_size, laptop_memory, laptop_weight, laptop_model, storage_amount, storage_type)
        VALUES(%s, %s, %s, %s, %s, %s)
        '''
        storage_values = (*composite_keys, amount, storage_type)

        cur.execute(storage_query, storage_values)
        conn.commit()

    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

    try:
        print("\nInserting into database table ports")
        print(
            f"laptop: {laptop_name}, Ethernet: {ethernet}, HDMI: {hdmi}, USB Type C: {usb_c}, Thunderbolt: {thunderbolt}")

        ports_query = '''
        INSERT INTO ports (laptop_screen_size, laptop_memory, laptop_weight, laptop_model, hdmi, ethernet, thunderbolt, type_c, display_port)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        ports_values = (*composite_keys, hdmi, ethernet, thunderbolt, usb_c, display_port)

        cur.execute(ports_query, ports_values)
        conn.commit()

    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

    try:
        print("\nInserting into database table screen")
        print(
            f"Laptop: {laptop_name}, Screen Resolution: {screen_res}, Refresh Rate: {refresh_rate}, Touch Screen: {touch_screen}")

        screen_query = '''
        INSERT INTO screen (laptop_screen_size, laptop_memory, laptop_weight, laptop_model, screen_resolution, refresh_rate, touch_screen)
        VALUES(%s, %s, %s, %s, %s, %s, %s)
        '''
        screen_values = (*composite_keys, screen_res, refresh_rate, touch_screen)

        cur.execute(screen_query, screen_values)
        conn.commit()

    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

    try:
        print("\nInserting into database table cpu:")
        print(f"Laptop: {laptop_name}, Brand: {cpu_brand}, CPU: {cpu_name}")

        cpu_query = '''
            INSERT INTO cpu (laptop_screen_size, laptop_memory, laptop_weight, laptop_model, model, brand)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        cpu_values = (*composite_keys, cpu_name, cpu_brand)

        cur.execute(cpu_query, cpu_values)
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
