import json
from pprint import pprint
from DBAccess.dbAccess import db_access


# Initialize dictionaries to store different laptop details
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
print("sorting through the JSON object lists\n")
for laptop in data:
    # Extract the tables from each laptop
    tables = laptop.get('tables', [])

    # Initialize dictionaries to store the details for each laptop
    laptop_details = {}
    brand_details = {}
    screen_details = {}
    processor_details = {}
    misc_details = {}
    features_details = {}
    ports_details = {}

    name_found = None

    # Loop through each table in the laptop
    # print("Adding table list items to their respected python dictionaries objects")
    for table in tables:
        title = table.get('title', '')
        table_data = table.get('data', {})

        # if name_found is None and "Name" in table_data:
        #     laptop_brand = table_data.get("Name", "")
        #     name_found = table_data["Name"]  # Stop checking for "Brand" in other tables
        #
        #
        # # this is here because the primary key for each of the tables is the laptop model, which means we need that to
        # # be able to insert it into the database
        #
        # # ensure every dictionary gets the first brand found, (name of the laptop when we get that)
        # if name_found:
        #     if name_found:
        #         brand_details["Name"] = name_found
        #         screen_details["Name"] = name_found
        #         processor_details["Name"] = name_found
        #         misc_details["Name"] = name_found
        #         features_details["Name"] = name_found
        #         ports_details["Name"] = name_found
        #     else:
        #         # Assign 'Unknown' if no brand is found
        #         # don't need to assign brand to the brand table, because well....
        #         screen_details["Name"] = "Unknown"
        #         processor_details["Name"] = "Unknown"
        #         misc_details["Name"] = "Unknown"
        #         features_details["Name"] = "Unknown"
        #         ports_details["Name"] = "Unknown"
        #
        # Organize the data based on the table title
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

    # Add the details to their respective lists
    # laptops.append(laptop_details)
    brands.append(brand_details)
    screens.append(screen_details)
    processors.append(processor_details)
    misc.append(misc_details)
    features.append(features_details)
    ports.append(ports_details)

print("Adding the dictionary items to their respected list objects")


# Print the lists to verify the data
print("\nBrands: \n")
pprint(brands)
# print("\nScreens: \n")


# pprint(screens)


# print("\nProcessors: \n")
# pprint(processors)
# print("\nMisc: \n")


# pprint(misc)


# print("\nFeatures: \n")


# pprint(features)


# print("\nPorts: \n")
# pprint(ports)


conn, cur = db_access()

'''
for the laptop insert table we need
# model - product details = Name
# brand os - Misc = Operating System
screensize - Screen - Size
price - 
# weight - product details = Weight
# batterylife - Misc = Battery Life
# memory - Misc = Memory Installed
'''

for i in range(len(brands)):
    # get each dict by index
    brand = brands[i] if i < len(brands) else{}
    item = misc[i] if i < len(misc) else {}
    screen = screens[i] if i < len(screens) else {}

    # extract the brand details
    name = brand.get('Name', '')
    weight = brand.get('Weight', '')
    laptop_brand = brand.get('Brand', '')

    price =1200

    # extract the misc details
    battery_life = item.get('Battery Life', '')
    memory_installed = item.get('Memory Installed', '')
    operating_system = item.get('Operating System,', '')

    # extract screen details
    screen_size = screen.get('Size', '')

    print("\nInserting into database table laptops:")
    print(f"Name: {name}, Weight: {weight}")
    print(f"Battery Life: {battery_life}, Memory Installed: {memory_installed}, OS: {operating_system}")
    print(f"Screen Size: {screen_size}")

    query = '''
        INSERT INTO laptops (model, brand, operatingsystem, screensize, price, weight, batterylife, memory)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    '''
    values = (name, laptop_brand, operating_system, screen_size, price, weight, battery_life, memory_installed)

    if conn and cur:
        try:
            cur.execute(query, values)
            conn.commit()
        except Exception as e:
            print(f"Database error: {e}")
    else:
        print(f"Data inserted successfully")

'''
inserting for the cpu table
laptop - name
model - name
brand - Brand
'''
for i in range(len(processors)):
    laptop = brands[i].get("Name", "")
    brand = processors[i].get("Brand", "")
    name = processors[i].get("Name", "")

    print("\nInserting into database table cpu:")
    print(f"Laptop: {laptop}")
    print(f"Brand: {brand}")
    print(f"COU: {name}")

    query = '''
        INSERT INTO cpu (laptop, model, brand)
        VALUES (%s, %s, %s)
    '''
    values = (laptop, name, brand)
    cur.execute(query, values)

    conn.commit()
    print("\nData inserted successfully")

'''
laptop name
bluetooth
num_pad
backlit
'''
for i in range(len(features)):
    laptop = brands[i].get("Name", "")
    bluetooth = features[i].get("Bluetooth", "")
    num_pad = features[i].get("Numeric Keyboard", "")
    backlit = features[i].get("Backlit Keyboard", "")

    print("\nInserting into database table features")
    print(f"Laptop: {laptop}")
    print(f"Bluetooth: {bluetooth}")
    print(f"Num Pad: {num_pad}")
    print(f"Backlit: {backlit}")

    query = '''
    INSERT INTO features (laptop, bluetooth, num_pad, backlit)
    VALUES (%s, %s, %s, %s)
    '''

    values =(laptop, bluetooth, num_pad, backlit)
    if conn and cur:
        try:
            cur.execute(query, values)
            conn.commit()
        except Exception as e:
            print(f"Database error: {e}")
    else:
        print(f"Data inserted successfully")
# checking if the objects exist
# if conn and cur:
#     try:

for i in range(len(brands)):
    cur.execute("ROLLBACK")  # Ensures the previous error does not affect this iteration
    laptop = brands[i].get("Name", "")
    gpu = misc[i].get("Graphics Card", "")
    if not gpu:
        print(f"Skipping GPU insertion for laptop: {laptop}, No GPU found")
    else:
        gpu_list = gpu.split(' ')
        gpu_brand = gpu_list[0]

    gpu_brand = gpu_list[0] if gpu_list else "None"
    gpu = gpu if gpu.lower() != "unknown" else "None"

    print("\nInserting into database table gpu")
    print(f"Laptop: {laptop}")
    print(f"GPU: {gpu}")
    print(f"Brand: {gpu_brand}")

    query = '''
    INSERT INTO gpu (laptop, model, brand)
    VALUES (%s, %s, %s)
    '''
    values = (laptop, gpu, gpu_brand)

    if conn and cur:
        try:
            cur.execute(query, values)
            conn.commit()
        except Exception as e:
            print(f"Database error: {e}")
            conn.rollback()
    else:
        print(f"Data inserted successfully")
