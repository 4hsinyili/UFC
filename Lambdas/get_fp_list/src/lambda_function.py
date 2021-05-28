#  for db control
from pymongo import MongoClient

# for file handling
import env

from FP_list import FPDinerListCrawler

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc_temp']


def lambda_handler(event, context, *args, **kwargs):
    target = {
        'title': 'Appworks School',
        'address': '110台北市信義區基隆路一段178號',
        'gps': (25.0424488, 121.562731)
    }
    list_crawler = FPDinerListCrawler()
    diners_count = list_crawler.main(target, db=db, collection='fp_list')
    return diners_count
