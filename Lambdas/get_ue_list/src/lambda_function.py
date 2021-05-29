#  for db control
from pymongo import MongoClient

# for file handling
import os
import env

# for timing and not to get caught
import time

from get_ue_list import UEDinerListCrawler

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc_temp']
driver_path = os.getcwd() + "/bin/headless-chromium"


def lambda_handler(event, context, *args, **kwargs):
    target = event
    # target = {
    #     "title": "Appworks School",
    #     "address": "110台北市信義區基隆路一段178號",
    #     "gps": (25.0424488, 121.562731)
    # }
    list_crawler = UEDinerListCrawler()
    diners_count = list_crawler.main(target, db=db, info_collection='ue_list')
    time.sleep(5)
    return diners_count