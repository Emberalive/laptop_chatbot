import json


laptops = []

with open('JSON.json', 'r') as file:
    data = json.load(file)

json_pretty = json.dumps(data, indent=4)

# print(json_pretty)

laptops.extend(data["laptops"])

print(laptops)