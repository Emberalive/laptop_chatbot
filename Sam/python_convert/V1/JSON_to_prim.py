import json


laptops = []

# opens the JSON file as read as a file
print("Reading the JSON file\n")
with open('JSON.json', 'r') as file:
    # loads the json objects as a variable (data)
    data = json.load(file)

# makes the print statement for the objects look readable
json_pretty = json.dumps(data, indent=4)

# print(json_pretty)
laptops.extend(data["laptops"])

print("JSON objects printed as a python list: \n")
print(laptops)