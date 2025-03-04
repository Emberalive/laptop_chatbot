import json
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
with open('scraped_data.json', 'r') as file:
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

# Insert laptops data into database
for i in range(len(brands)):
    cur.execute("ROLLBACK")  # Ensure previous errors don't affect this iteration

    # Extract details from dictionaries
    brand = brands[i] if i < len(brands) else {}
    item = misc[i] if i < len(misc) else {}
    screen = screens[i] if i < len(screens) else {}

    name = brand.get('Name', '')
    weight = brand.get('Weight', '')
    laptop_brand = brand.get('Brand', '')
    battery_life = item.get('Battery Life', '')
    memory_installed = item.get('Memory Installed', '')
    operating_system = item.get('Operating System', '')
    screen_size = screen.get('Size', '')
    price = 1200  # Default price (consider making this dynamic)

    print("\nInserting into database table laptops:")
    print(
        f"Name: {name}, Weight: {weight}, Battery Life: {battery_life}, Memory Installed: {memory_installed}, OS: {operating_system}, Screen Size: {screen_size}")

    query = '''
        INSERT INTO laptops (model, brand, operatingsystem, screensize, price, weight, batterylife, memory)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    '''
    values = (name, laptop_brand, operating_system, screen_size, price, weight, battery_life, memory_installed)

    try:
        cur.execute(query, values)
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

# Insert CPU data into database
for i in range(len(processors)):
    cur.execute("ROLLBACK")

    laptop = brands[i].get("Name", "")
    brand = processors[i].get("Brand", "")
    name = processors[i].get("Name", "")

    print("\nInserting into database table cpu:")
    print(f"Laptop: {laptop}, Brand: {brand}, CPU: {name}")

    query = '''
        INSERT INTO cpu (laptop, model, brand)
        VALUES (%s, %s, %s)
    '''
    values = (laptop, name, brand)

    try:
        cur.execute(query, values)
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

# Insert Features data into database
for i in range(len(features)):
    cur.execute("ROLLBACK")

    laptop = brands[i].get("Name", "")
    bluetooth = features[i].get("Bluetooth", "")
    num_pad = features[i].get("Numeric Keyboard", "")
    backlit = features[i].get("Backlit Keyboard", "")

    print("\nInserting into database table features")
    print(f"Laptop: {laptop}, Bluetooth: {bluetooth}, Num Pad: {num_pad}, Backlit: {backlit}")

    query = '''
        INSERT INTO features (laptop, bluetooth, num_pad, backlit)
        VALUES (%s, %s, %s, %s)
    '''
    values = (laptop, bluetooth, num_pad, backlit)

    try:
        cur.execute(query, values)
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

# Insert GPU data into database
for i in range(len(brands)):
    cur.execute("ROLLBACK")

    laptop = brands[i].get("Name", "")
    gpu = misc[i].get("Graphics Card", "")

    if not gpu:
        print(f"Skipping GPU insertion for laptop: {laptop}, No GPU found")
        continue

    gpu_list = gpu.split(' ')
    gpu_brand = gpu_list[0] if gpu_list else None
    gpu = gpu if gpu.lower() != "unknown" else None

    print("\nInserting into database table gpu")
    print(f"Laptop: {laptop}, GPU: {gpu}, Brand: {gpu_brand}")

    query = '''
        INSERT INTO gpu (laptop, model, brand)
        VALUES (%s, %s, %s)
    '''
    values = (laptop, gpu, gpu_brand)

    try:
        cur.execute(query, values)
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

# inserting memory data into database
for i in range(len(brands)):
    cur.execute("ROLLBACK")

    laptop = brands[i].get("Name", "")
    storage = misc[i].get("Storage", "")

    storage_list = storage.split(" ")
    amount = storage_list[0]
    storage_type = storage_list[1]


    print("\nInserting into database table memory")
    print(f"laptop: {laptop}, Storage Amount: {amount}, Storage Type: {storage_type}")

    query = '''
    INSERT INTO memory (laptop, storage_amount, storage_type)
    VALUES(%s, %s, %s)
    '''
    values = (laptop, amount, storage_type)

    try:
        cur.execute(query, values)
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

# Inserting ports data into table database
for i in range(len(brands)):
    cur.execute("ROLLBACK")

    laptop = brands[i].get("Name", "")

    ethernet = ports[i].get("Ethernet (RJ45)", "None")
    hdmi = ports[i].get("HDMI", "None")
    usb_c = ports[i].get("USB Type-C", "None")
    thunderbolt = ports[i].get("Thunderbolt", "None")
    display_port = ports[i].get("Display Port", "None")

    # print("\nConverting all values into String rather than boolean")
    #
    # Ethernet = str(ethernet)
    # HDMI = str(hdmi)
    # USB_C = str(usb_c)
    # Thunderbolt = str(thunderbolt)
    # Display_Port = str(display_port)

    print("\nInserting into database table ports")
    print(f"laptop: {laptop}, Ethernet: {ethernet}, HDMI: {hdmi}, USB Type C: {usb_c}, Thunderbolt: {thunderbolt}")

    query = '''
    INSERT INTO ports (laptop, hdmi, ethernet, thunderbolt, typec, display_port)
    VALUES (%s, %s, %s, %s, %s, %s)
    '''
    values = (laptop, hdmi, ethernet, thunderbolt, usb_c, display_port)
    # values = (laptop, HDMI, Ethernet, Thunderbolt, USB_C, Display_Port)

    try:
        cur.execute(query, values)
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()

for i in range(len(brands)):
    cur.execute("ROLLBACK")

    laptop = brands[i].get("Name", "")

    screen_res = screens[i].get("Resolution", "Unknown")
    refresh_rate = screens[i].get("Refresh Rate", "Unknown")
    touch_screen = screens[i].get("Touchscreen", "Unknown")

    print("\nInserting into database table screen")
    print(f"Screen Resolution: {screen_res}, Refresh Rate: {refresh_rate}, Touch Screen: {touch_screen}")

    query = '''
    INSERT INTO screen (laptop, screen_res, refresh, touch_screen)
    VALUES(%s, %s, %s, %s)
    '''

    values = (laptop, screen_res, refresh_rate, touch_screen)

    try:
        cur.execute(query, values)
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()


