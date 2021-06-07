#  for db control
from pymongo import MongoClient

# for file handling
import env
import time

from get_ue_detail import UEDinerDetailCrawler

MONGO_ATLAS_URI = env.MONGO_ATLAS_URI
admin_client = MongoClient(MONGO_ATLAS_URI)
db = admin_client['ufc']


def lambda_handler(event, context, *args, **kwargs):
    index = event
    # index = {"offset": 0, "limit": 10}
    offset = index['offset']
    limit = index['limit']
    sleepy = index['sleep']
    time.sleep(sleepy)
    detail_crawler = UEDinerDetailCrawler(db, 'ue_list_temp', offset, limit)
    diners, error_logs = detail_crawler.main(collection='ue_detail')
    return len(diners)
