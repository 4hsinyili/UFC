import env
from pymongo import MongoClient
import pprint

MONGO_ATLAS_URI = env.MONGO_ATLAS_URI
admin_client = MongoClient(MONGO_ATLAS_URI)
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

result = db['gm_reviews'].aggregate(pipeline=pipeline, allowDiskUse=True)
result = list(result)[0]['_id']
pprint.pprint(result[0])
