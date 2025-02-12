import json
from pprint import pprint

# Initialize lists to store different laptop details
laptops = []
brands = []
screens = []
processors = []
misc = []
features = []
ports = []

# Load the JSON data from the file
with open('scraped_data.json', 'r') as file:
    data = json.load(file)

# Loop through each laptop in the JSON data
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

    # Loop through each table in the laptop
    for table in tables:
        title = table.get('title', '')
        table_data = table.get('data', {})

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
    laptops.append(laptop_details)
    brands.append(brand_details)
    screens.append(screen_details)
    processors.append(processor_details)
    misc.append(misc_details)
    features.append(features_details)
    ports.append(ports_details)

# Print the lists to verify the data
print("Brands:")
pprint(brands)
print("Screens:")
pprint(screens)
print("Processors:")
pprint(processors)
print("Misc:")
pprint(misc)
print("Features:")
pprint(features)
print("Ports:")
pprint(ports)
