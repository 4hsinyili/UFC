#  for db control
from pymongo import MongoClient

# for file handling
import env

from dispatch_ue_diners import UEDinerDispatcher

MONGO_EC2_URI = env.MONGO_EC2_URI
admin_client = MongoClient(MONGO_EC2_URI)

db = admin_client['ufc']


def lambda_handler(event, context):
    lamdas_count = 14

    dispatcher = UEDinerDispatcher(db, 'ue_list')
    diners_count = dispatcher.main()
    print('There are ', diners_count, ' diners in ue_list_temp.')

    divider = diners_count // lamdas_count
    print('Now each get_ue_detail will fetch ', divider, ' results.')
    offsets = [i * divider for i in range(lamdas_count)]
    limits = [divider for i in range(lamdas_count - 1)]
    remainder = diners_count - offsets[-1]
    limits.append(remainder)
    sleep_list = [i for i in range(lamdas_count)]
    indexes = [{'offset': offsets[i], 'limit': limits[i], 'sleep': sleep_list[i]} for i in range(lamdas_count)]

    return indexes
