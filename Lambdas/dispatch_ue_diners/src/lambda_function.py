#  for db control
from pymongo import MongoClient

# for file handling
import env

from dispatch_ue_diners import UEDinerDispatcher

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc_temp']


def lambda_handler(event, context):
    lamdas_count = 14
    diners_counts = sum(event['taskresult'])
    divider = diners_counts // lamdas_count
    offsets = [i * divider for i in range(lamdas_count)]
    limits = [divider for i in range(lamdas_count - 1)]
    remainder = diners_counts - offsets[-1]
    limits.append(remainder)
    sleep_list = [i for i in range(lamdas_count)]
    indexes = [{'offset': offsets[i], 'limit': limits[i], 'sleep': sleep_list[i]} for i in range(lamdas_count)]

    crawler = UEDinerDispatcher('ue_list')
    crawler.save_to_temp_collection()
    return indexes
