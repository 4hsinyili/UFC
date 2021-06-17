#  for db control
from pymongo import MongoClient

# for file handling
import env
import conf
import utils
from crawl_fp import FPDinerListCrawler

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
    list_crawler = FPDinerListCrawler(TARGET,
                                      LIST_URL,
                                      HEADERS,
                                      db,
                                      write_collection=LIST_COLLECTION,
                                      log_collection=LOG_COLLECTION,
                                      w_triggered_by=GET_FP_LIST,
                                      offset=0,
                                      limit=API_LIMIT)
    diners_count = list_crawler.main()
    return diners_count
