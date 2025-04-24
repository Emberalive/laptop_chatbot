import json

from DBAccess.dbAccess import get_db_connection
from DBAccess.dbAccess import release_db_connection

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

# desktop path
# with open('/home/sammy/Documents/2_brighton/sem2/groupProject-laptopChatBox/laptop_chatbot/Sam/server_side/scrapers/scraped_data/scraped_data.json', 'r') as file:
#     data = json.load(file)

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
conn, cur = get_db_connection()

print("\nClearing the database, so that new data can be inserted")
try:
    print("\nDeleting from table: configuration_storage")
    storage_config_delete = "DELETE FROM configuration_storage"
    cur.execute(storage_config_delete)

    print("\nDeleting from table: features")
    features_delete = "DELETE FROM features"
    cur.execute(features_delete)

    print("\nDeleting from table: ports")
    ports_delete = "DELETE FROM ports"
    cur.execute(ports_delete)

    print("\nDeleting from table: screens")
    screens_delete = "DELETE FROM screens"
    cur.execute(screens_delete)

    print("\nDeleting from table: laptop_configurations")
    laptop_config_delete = "DELETE FROM laptop_configurations"
    cur.execute(laptop_config_delete)


    print("\nDeleting from table: processors")
    processors_delete = "DELETE FROM processors"
    cur.execute(processors_delete)

    print("\nDeleting from table: graphics_cards")
    graphics_cards_delete = "DELETE FROM graphics_cards"
    cur.execute(graphics_cards_delete)

    print("\nresetting confg_id auto increment value")
    configuration_laptops_reset = "ALTER SEQUENCE laptop_configurations_config_id_seq RESTART WITH 1"
    cur.execute(configuration_laptops_reset)

    print("\nDeleting from able laptop_model")
    laptop_model_delete = "DELETE FROM laptop_models"
    cur.execute(laptop_model_delete)

    print("\nresetting model_id auto increment value")
    laptop_model_reset = "ALTER SEQUENCE laptop_models_model_id_seq RESTART WITH 1"
    cur.execute(laptop_model_reset)

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

    bluetooth = feature.get("Bluetooth", False)
    num_pad = features[i].get("Numeric Keyboard", False)
    backlit = features[i].get("Backlit Keyboard", False)

    gpu = spec.get("Graphics Card", "")

    if not gpu:
        print(f"Skipping GPU insertion for laptop: {laptop_name}, No GPU found")

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

    ethernet = ports[i].get("Ethernet (RJ45)", False)
    hdmi = ports[i].get("HDMI", False)
    usb_c = ports[i].get("USB Type-C", False)
    thunderbolt = ports[i].get("Thunderbolt", False)
    display_port = ports[i].get("Display Port", False)

    screen_res = screens[i].get("Resolution", "Unknown")
    refresh_rate = screens[i].get("Refresh Rate", "Unknown")
    touch_screen = screens[i].get("Touchscreen", False)


    #Inserting the processor table
    try:
        print(f"\nChecking if cpu: {cpu_name} is in the database")
        check_cpu = "SELECT model FROM processors WHERE model = %s"
        cpu_check_values = (cpu_name,)
        cur.execute(check_cpu, cpu_check_values)

        result = cur.fetchone()
        if result is None:
            print("\nInserting into database table processors:")
            print(f"Model: {cpu_name}, Brand: {cpu_brand}")
            cpu_querey = ("INSERT INTO processors (brand, model)"
                          "VALUES(%s, %s)")
            cpu_values = (cpu_brand, cpu_name)
            cur.execute(cpu_querey, cpu_values)
            conn.commit()
        else:
            cpu_id = result[0]  # Get existing ID
            print(f"\nCPU already exists (CPU: {cpu_id})")

    except Exception as e:
        conn.rollback()
        print(f"There was an error with inserting into processors: {e}")

    #Inerting into the table gpu
    try:
        print(f"\nChecking if gpu: {gpu} is i the database")
        check_gpu = "SELECT model FROM graphics_cards WHERE model = %s"
        gpu_check_values = (gpu,)
        cur.execute(check_gpu, gpu_check_values)

        result = cur.fetchone()
        if result is None:
            print("\nInserting into database table graphics_cards:")
            print(f"Model: {gpu}, Brand: {gpu_brand}")
            gpu_query = ("INSERT INTO graphics_cards (brand, model)"
                         "VALUES(%s, %s)")
            gpu_values = (gpu_brand, gpu)
            cur.execute(gpu_query, gpu_values)
            conn.commit()
        else:
            gpu_id =result[0]
            print(f"\nGPU already exists (GPU: {gpu_id})")

    except Exception as e:
        conn.rollback()
        print(f"There was an error inserting into graphics cards: {e}")

    config_id = None

    #Inserting into the laptop model and laptop configurations
    try:
        print(f"Checking if there is already {laptop_name} in the database")
        laptop_querey = "SELECT * FROM laptop_models WHERE model_name = %s"
        laptop_Values = (laptop_name,)
        cur.execute(laptop_querey, laptop_Values)

        results = cur.fetchone()
        if (model_row := cur.fetchone()):
            print(f"\nThe Model: {laptop_name} already exists")
            model_id = results[0]
        else:
            print(f"\nThe model: {laptop_name} is not in the database")

            print("\nInserting into database table laptop_models")
            cur.execute(
                "INSERT INTO laptop_models (brand, model_name) VALUES (%s, %s) RETURNING model_id",
                (laptop_brand, laptop_name)
            )
            model_id = cur.fetchone()[0]
            conn.commit()
            print(f"Inserted new model with ID: {model_id}")


        print("\nInserting into table laptop_configurations")
        print(
            f"Price: {price}, Weight: {weight}, Battery Life: {battery_life}, Memory: {memory_installed}, OS: {operating_system}, Processor: {cpu_name}, Graphics Card: {gpu}")
        laptop_configuration_query = (
            "INSERT INTO laptop_configurations (model_id, price, weight, battery_life, memory_installed, operating_system, processor, graphics_card)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            "RETURNING config_id")
        laptop_configuration_values = (model_id, price, weight, battery_life, memory_installed, operating_system, cpu_name, gpu)
        cur.execute(laptop_configuration_query, laptop_configuration_values)
        config_id = cur.fetchone()[0]
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"error Inserting into laptop_configurations: {e}")

    #Inserting into the storage tables
    try:
        print("\nInserting into database table configuration_storage")
        print(f"Config ID: {config_id}, Storage Media: {storage_type}, Capacity: {amount}")
        configuration_storage_querey = ("INSERT INTO configuration_storage (config_id, storage_type, capacity)"
                                        "VALUES(%s, %s, %s)")
        configuration_storage_values = (config_id, storage_type, amount)
        cur.execute(configuration_storage_querey, configuration_storage_values)
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Error inserting storage configuration: {e}")

    #Inserting into the features table
    try:
        print("\nInserting into database table features")
        print(f"Config ID: {config_id}, Backlit Keyboard: {backlit}, Num Pad: {num_pad}, Bluetooth: {bluetooth}")
        features_querey = ("INSERT INTO features (config_id, backlit_keyboard, numeric_keyboard, bluetooth)"
                           "VALUES(%s, %s, %s, %s)")
        features_values = (config_id, backlit, num_pad, bluetooth)
        cur.execute(features_querey, features_values)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"error inserting into features: {e}")


    #Inserting into the ports table
    try:
        print("\nInserting into database table ports")
        print(f"Config ID: {config_id} Ethernet: {ethernet}, HDMI: {hdmi}, USB - C: {usb_c}, Thunderbolt: {thunderbolt}, Display Port: {display_port}")
        ports_querey = ("INSERT INTO ports (config_id, ethernet, hdmi, usb_type_c, thunderbolt, display_port)"
                        "VALUES(%s, %s, %s, %s, %s, %s)")
        ports_values = (config_id, ethernet, hdmi, usb_c, thunderbolt, display_port)
        cur.execute(ports_querey, ports_values)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"error with the database and that: {e}")

    #Inserting into the screens table
    try:
        print("\nInserting into database table screens")
        print(f"Config ID: {config_id}, Size: {screen_size}, Resolution: {screen_res}, Touchscreen: {touch_screen}, Refresh Rate: {refresh_rate}")
        screens_querey = ("INSERT INTO screens (config_id, size, resolution, touchscreen, refresh_rate)"
                          "VALUES(%s, %s, %s, %s, %s)")
        screen_values = (config_id, screen_size, screen_res, touch_screen, refresh_rate)
        cur.execute(screens_querey, screen_values)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"error and that i guess: {e}")
release_db_connection(conn, cur)