# for db control
from pymongo import MongoClient, UpdateOne

# for crawling from API
import requests

# for file handling
import os
from dotenv import load_dotenv
import json

# for timing and not to get caught
import time
import random
from datetime import datetime
import os
# for preview
import pprint

from UE_crawl import UEDinerListCrawler

load_dotenv()
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT"))
MONGO_ADMIN_USERNAME = os.getenv("MONGO_ADMIN_USERNAME")
MONGO_ADMIN_PASSWORD = os.getenv("MONGO_ADMIN_PASSWORD")

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc_temp']
driver_path = os.getcwd() + "/bin/headless-chromium"

target = {
    'name': 'Appworks School',
    'address': '110台北市信義區基隆路一段178號',
    'gps': (25.0424488, 121.562731)
}


def lambda_handler(*args, **kwargs):
    start = time.time()
    list_crawler = UEDinerListCrawler()
    list_crawler.main(target, db=db, html_collection='ue_html', responses_collection='ue_responses', info_collection='ue_list')
    stop = time.time()
    pprint.pprint(stop - start)
    time.sleep(5)
