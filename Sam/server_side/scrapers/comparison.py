from deepdiff import DeepDiff
import json
import pprint

with open('/home/samuel/laptop_chatbot/Sam/server_side/scrapers/scraped_data/latest.json') as f1, \
     open('/home/samuel/laptop_chatbot/Sam/server_side/scrapers/scraped_data/old_data/scrape_2025-05-05.json') as f2:
    data1 = json.load(f1)
    data2 = json.load(f2)

diff = DeepDiff(data1, data2, verbose_level=2)
pprint(diff)