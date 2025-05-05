from deepdiff import DeepDiff
import json
import pprint
import sys
from loguru import logger

logger.add(sys.stdout, format="{time} {level} {message}")
logger.add("../logs/comparison.log", rotation="10 MB", retention="35 days", compression="zip")
logger = logger.bind(user="comparer")

logger.info(f"starting the comparison between the od and new json files")
try:
    with open('/home/samuel/laptop_chatbot/Sam/server_side/scrapers/scraped_data/latest.json') as f1, \
         open('/home/samuel/laptop_chatbot/Sam/server_side/scrapers/scraped_data/old_data/scrape_2025-05-05.json') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    diff = DeepDiff(data1, data2, verbose_level=2)

    logger.info("comparison completed")

    pprint.pprint(diff)
except Exception as e:
    logger.error(f"error in attempting to compare the old and new json data {e}")
pprint.pprint(diff)