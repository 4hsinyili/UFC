#  for db control
from pymongo import MongoClient

# for file handling
import env
import time

from get_fp_detail import FPDinerDetailCrawler

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc_temp']

target = {
    'title': 'Appworks School',
    'address': '110台北市信義區基隆路一段178號',
    'gps': (25.0424488, 121.562731)
}


def lambda_handler(event, context, *args, **kwargs):
    index = event
    # index = {'offset': 0, 'limit': 10}
    offset = index['offset']
    limit = index['limit']
    sleepy = index['sleep']
    time.sleep(sleepy)
    detail_crawler = FPDinerDetailCrawler(target, 'fp_list', offset, limit)
    diners, error_logs = detail_crawler.main(db=db, collection='fp_detail')
    return len(diners)
