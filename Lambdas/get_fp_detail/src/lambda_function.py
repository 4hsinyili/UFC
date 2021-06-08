#  for db control
from pymongo import MongoClient

# for file handling
import env
import time

from get_fp_detail import FPDinerDetailCrawler

MONGO_EC2_URI = env.MONGO_EC2_URI
admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client['ufc']

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
    detail_crawler = FPDinerDetailCrawler(target, db, 'fp_list_temp', offset, limit)
    diners, error_logs = detail_crawler.main(collection='fp_detail')
    return len(diners)
