#  for db control
from pymongo import MongoClient

# for file handling
import env
import time
import utils
import conf
from crawl_fp import FPDinerDetailCrawler

MONGO_EC2_URI = env.MONGO_EC2_URI
DB_NAME = conf.DB_NAME
LIST_COLLECTION = conf.FP_LIST_COLLECTION
LIST_TEMP_COLLECTION = conf.FP_LIST_TEMP_COLLECTION
DETAIL_COLLECTION = conf.FP_DETAIL_COLLECTION
LOG_COLLECTION = conf.LOG_COLLECTION
GET_FP_LIST = conf.GET_FP_LIST
GET_FP_DETAIL = conf.GET_FP_DETAIL

API_JSON = utils.read_json('api_fp.json')
HEADERS = API_JSON['headers']
LIST_URL = API_JSON['list_url']
DETAIL_URL = API_JSON['detail_url']
DELIVER_FEE_URL = API_JSON['deliver_fee_url']
API_LIMIT = API_JSON['API_LIMIT']
TARGET = utils.read_json('target_fp.json')

admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client[DB_NAME]


def lambda_handler(event, context, *args, **kwargs):
    index = event
    # index = {'offset': 0, 'limit': 10}
    offset = index['offset']
    limit = index['limit']
    sleepy = index['sleep']
    time.sleep(sleepy)
    detail_crawler = FPDinerDetailCrawler(
            TARGET,
            DETAIL_URL,
            DELIVER_FEE_URL,
            HEADERS,
            db,
            read_collection=LIST_TEMP_COLLECTION,
            write_collection=DETAIL_COLLECTION,
            log_collection=LOG_COLLECTION,
            r_triggered_by=GET_FP_LIST,
            w_triggered_by=GET_FP_DETAIL,
            offset=offset,
            limit=limit)
    diners, error_logs = detail_crawler.main(collection='fp_detail')
    return len(diners)
