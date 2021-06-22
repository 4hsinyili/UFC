#  for db control
from pymongo import MongoClient

# for file handling
import env
import conf
import utils

# for timing and not to get caught
import time

from crawl_ue import UEDinerListCrawler

MONGO_EC2_URI = env.MONGO_EC2_URI
DRIVER_PATH = env.DRIVER_PATH
DB_NAME = conf.DB_NAME

LIST_COLLECTION = conf.UE_LIST_COLLECTION
LIST_TEMP_COLLECTION = conf.UE_LIST_TEMP_COLLECTION
DETAIL_COLLECTION = conf.UE_DETAIL_COLLECTION
LOG_COLLECTION = conf.LOG_COLLECTION
GET_UE_LIST = conf.GET_UE_LIST
GET_UE_DETAIL = conf.GET_UE_DETAIL

API_JSON = utils.read_json('api_ue.json')
HEADERS = API_JSON['headers']
DETAIL_URL = API_JSON['detail_url']
TARGETS = utils.read_json('targets_ue.json')

admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client[DB_NAME]


def lambda_handler(event, context, *args, **kwargs):
    target = event
    # target = {
    #     "title": "Appworks School",
    #     "address": "110台北市信義區基隆路一段178號",
    #     "gps": (25.0424488, 121.562731)
    # }
    list_crawler = UEDinerListCrawler(target,
                                      db,
                                      write_collection=LIST_COLLECTION,
                                      log_collection=LOG_COLLECTION,
                                      w_triggered_by=GET_UE_LIST,
                                      headless=True,
                                      auto_close=True,
                                      inspect=False)
    diners_count = list_crawler.main()
    time.sleep(5)
    return diners_count
