#  for db control
from pymongo import MongoClient

# for file handling
import env

from get_fp_list import FPDinerListCrawler

MONGO_ATLAS_URI = env.MONGO_ATLAS_URI
admin_client = MongoClient(MONGO_ATLAS_URI)
db = admin_client['ufc']


def lambda_handler(event, context, *args, **kwargs):
    target = {
        'title': 'Appworks School',
        'address': '110台北市信義區基隆路一段178號',
        'gps': (25.0424488, 121.562731)
    }
    list_crawler = FPDinerListCrawler()
    diners_count = list_crawler.main(target, db=db, collection='fp_list')
    return diners_count
