import env
from pymongo import MongoClient
import pprint

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc_temp']

pipeline = [
    {'$sort': {'time': -1}},
    {'$group': {
        '_id': '$data',
        'time': {'$last': '$time'}
    }}, {
        '$limit': 1
    }
]

result = db['ue_detail'].aggregate(pipeline=pipeline, allowDiskUse=True)
result = list(result)[0]['_id']
pprint.pprint(result[1])
