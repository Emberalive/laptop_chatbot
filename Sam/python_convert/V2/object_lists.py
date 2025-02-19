import json
from pprint import pprint

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

    brand_found = None

    # Loop through each table in the laptop
    # print("Adding table list items to their respected python dictionaries objects")
    for table in tables:
        title = table.get('title', '')
        table_data = table.get('data', {})

        if brand_found is None and "Brand" in table_data:
            laptop_brand = table_data.get("Brand", "")
            brand_found = table_data["Brand"]  # Stop checking for "Brand" in other tables


        # this is here because the primary key for each of the tables is the laptop model, which means we need that to
        # be able to insert it into the database

        # ensure every dictionary gets the first brand found, (name of the laptop when we get that)
        if brand_found:
            if brand_found:
                brand_details["Brand"] = brand_found
                screen_details["Brand"] = brand_found
                processor_details["Brand"] = brand_found
                misc_details["Brand"] = brand_found
                features_details["Brand"] = brand_found
                ports_details["Brand"] = brand_found
            else:
                # Assign 'Unknown' if no brand is found
                # don't need to assign brand to the brand table, because well....
                screen_details["Brand"] = "Unknown"
                processor_details["Brand"] = "Unknown"
                misc_details["Brand"] = "Unknown"
                features_details["Brand"] = "Unknown"
                ports_details["Brand"] = "Unknown"

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
print("\nScreens: \n")
pprint(screens)
print("\nProcessors: \n")
pprint(processors)
print("\nMisc: \n")
pprint(misc)
print("\nFeatures: \n")
pprint(features)
print("\nPorts: \n")
pprint(ports)