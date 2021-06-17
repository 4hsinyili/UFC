#  for db control
from pymongo import MongoClient

# for file handling
import env
import time
import conf
import utils

from crawl_ue import UEDinerDetailCrawler

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
    index = event
    # index = {"offset": 0, "limit": 10}
    offset = index['offset']
    limit = index['limit']
    sleepy = index['sleep']
    time.sleep(sleepy)
    detail_crawler = UEDinerDetailCrawler(
            HEADERS,
            DETAIL_URL,
            db,
            read_collection=LIST_TEMP_COLLECTION,
            write_collection=DETAIL_COLLECTION,
            log_collection=LOG_COLLECTION,
            r_triggered_by=GET_UE_LIST,
            w_triggered_by=GET_UE_DETAIL,
            offset=offset,
            limit=limit)
    diners, error_logs = detail_crawler.main(collection='ue_detail')
    return len(diners)
