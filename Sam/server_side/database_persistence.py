import json
from distutils.util import execute
from pprint import pprint
from DBAccess.dbAccess import db_access

# Initialize lists to store different laptop details
laptops = []
brands = []
screens = []
processors = []
misc = []
features = []
ports = []

# Load the JSON data from the file
print("Opening the scraped data\n")
with open('/home/samuel/Documents/2_Brighton/sem2/GroupProject/laptop_chatbot/Sam/server_side/scrapers/scraped_data/scraped_data.json', 'r') as file:
    data = json.load(file)



# Loop through each laptop in the JSON data
print("Sorting through the JSON object lists\n")
for laptop in data:
    tables = laptop.get('tables', [])  # Extract tables from each laptop

    # Initialize dictionaries for each category
    brand_details = {}
    screen_details = {}
    processor_details = {}
    misc_details = {}
    features_details = {}
    ports_details = {}

    # Loop through each table and store data in respective dictionaries
    for table in tables:
        title = table.get('title', '')
        table_data = table.get('data', {})

        if title == 'Product Details':
            brand_details.update(table_data)
        elif title == 'Screen':
            screen_details.update(table_data)
        elif title == 'Processor':
            processor_details.update(table_data)
        elif title == 'Misc':
            misc_details.update(table_data)
        elif title == 'Features':
            features_details.update(table_data)
        elif title == 'Ports':
            ports_details.update(table_data)

    # Append extracted details to their respective lists
    brands.append(brand_details)
    screens.append(screen_details)
    processors.append(processor_details)
    misc.append(misc_details)
    features.append(features_details)
    ports.append(ports_details)

print("Adding the dictionary items to their respective list objects")

# Print extracted brands for verification
print("\nBrands: \n")
pprint(brands)

# Establish database connection
conn, cur = db_access()

print("\nClearing the database, so that new data can be inserted")
try:
    print("\nDeleting from laptops")
    delete_laptops = "DELETE FROM laptops"
    cur.execute(delete_laptops)
    conn.commit()

    print("\nDeleting from features")
    delete_features = "DELETE FROM features;"

    cur.execute(delete_features)
    conn.commit()

    print("\nDeleting from gpu")
    delete_gpu  = "DELETE FROM gpu;"
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
except Exception as e:
    print(f"Database error: {e}")
    conn.rollback()

for i in range(len(brands)):
    brand = brands[i] if i < len(brands) else {}
    item = misc[i] if i < len(misc) else {}
    screen = screens[i] if i < len(screens) else {}

    laptop_name = brand.get('Name', '')
    weight = brand.get('Weight', '')
    laptop_brand = brand.get('Brand', '')
    battery_life = item.get('Battery Life', '')
    memory_installed = item.get('Memory Installed', '')
    operating_system = item.get('Operating System', '')
    screen_size = screen.get('Size', '')
    price = 1200

    cpu_brand = processors[i].get("Brand", "")
    cpu_name = processors[i].get("Name", "")

    bluetooth = features[i].get("Bluetooth", "")
    num_pad = features[i].get("Numeric Keyboard", "")
    backlit = features[i].get("Backlit Keyboard", "")

    gpu = misc[i].get("Graphics Card", "")

    if not gpu:
        print(f"Skipping GPU insertion for laptop: {laptop}, No GPU found")

    gpu_list = gpu.split(' ')
    gpu_brand = gpu_list[0] if gpu_list else "Unknown"
    gpu = gpu if gpu.lower() != "unknown" else "None"

    storage = misc[i].get("Storage", "")

    storage_list = storage.split(" ")
    amount = storage_list[0]
    storage_type = storage_list[1]

    storage = misc[i].get("Storage", "")
    storage_list = storage.split(" ")
    amount = storage_list[0]
    storage_type = storage_list[1]

    ethernet = ports[i].get("Ethernet (RJ45)", "None")
    hdmi = ports[i].get("HDMI", "None")
    usb_c = ports[i].get("USB Type-C", "None")
    thunderbolt = ports[i].get("Thunderbolt", "None")
    display_port = ports[i].get("Display Port", "None")

    screen_res = screens[i].get("Resolution", "Unknown")
    refresh_rate = screens[i].get("Refresh Rate", "Unknown")
    touch_screen = screens[i].get("Touchscreen", "Unknown")


    print("\nInserting into database table laptops:")
    print(f"Name: {laptop_name}, Weight: {weight}, Battery Life: {battery_life}, Memory Installed: {memory_installed}, OS: {operating_system}, Screen Size: {screen_size}")

    laptop_query = '''
        INSERT INTO laptops (model, brand, operating_system, screen_size, price, weight, battery_life, memory_installed)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    '''
    laptop_values = (laptop_name, laptop_brand, operating_system, screen_size, price, weight, battery_life, memory_installed)

    print("\nInserting into database table features")
    print(f"Laptop: {laptop_name}, Bluetooth: {bluetooth}, Num Pad: {num_pad}, Backlit: {backlit}")

    features_query = '''
        INSERT INTO features (laptop_model, bluetooth, num_pad, backlit_keyboard)
        VALUES (%s, %s, %s, %s)
    '''
    features_values = (laptop_name, bluetooth, num_pad, backlit)

    print("\nInserting into database table gpu")
    print(f"Laptop: {laptop_name}, GPU: {gpu}, Brand: {gpu_brand}")

    gpu_query = '''
        INSERT INTO gpu (laptop_model, model, brand)
        VALUES (%s, %s, %s)
    '''
    gpu_values = (laptop_name, gpu, gpu_brand)

    print("\nInserting into database table storage")
    print(f"laptop: {laptop_name}, Storage Amount: {amount}, Storage Type: {storage_type}")

    storage_query = '''
    INSERT INTO storage (laptop_model, storage_amount, storage_type)
    VALUES(%s, %s, %s)
    '''
    storage_values = (laptop_name, amount, storage_type)

    print("\nInserting into database table ports")
    print(f"laptop: {laptop_name}, Ethernet: {ethernet}, HDMI: {hdmi}, USB Type C: {usb_c}, Thunderbolt: {thunderbolt}")

    ports_query = '''
    INSERT INTO ports (laptop_model, hdmi, ethernet, thunderbolt, type_c, display_port)
    VALUES (%s, %s, %s, %s, %s, %s)
    '''
    ports_values = (laptop_name, hdmi, ethernet, thunderbolt, usb_c, display_port)

    print("\nInserting into database table screen")
    print(f"Laptop: {laptop_name}, Screen Resolution: {screen_res}, Refresh Rate: {refresh_rate}, Touch Screen: {touch_screen}")

    screen_query = '''
    INSERT INTO screen (laptop_model, screen_resolution, refresh_rate, touch_screen)
    VALUES(%s, %s, %s, %s)
    '''

    screen_values = (laptop_name, screen_res, refresh_rate, touch_screen)

    print("\nInserting into database table cpu:")
    print(f"Laptop: {laptop_name}, Brand: {cpu_brand}, CPU: {cpu_name}")

    cpu_query = '''
        INSERT INTO cpu (laptop_model, model, brand)
        VALUES (%s, %s, %s)
    '''
    cpu_values = (laptop_name, cpu_name, cpu_brand)

    try:
        cur.execute(laptop_query, laptop_values)
        conn.commit()

        cur.execute(features_query, features_values)
        conn.commit()

        cur.execute(gpu_query, gpu_values)
        conn.commit()

        cur.execute(storage_query, storage_values)
        conn.commit()

        cur.execute(ports_query, ports_values)
        conn.commit()

        cur.execute(screen_query, screen_values)
        conn.commit()

        cur.execute(cpu_query, cpu_values)
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()