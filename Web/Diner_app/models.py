import pprint
import copy
import env
from pymongo import MongoClient
import time

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc_temp']
# Create your models here.


class UEChecker():
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection

    def get_latest_records(self, pipeline, offset=0, limit=0):
        db = self.db
        collection = self.collection
        pipeline = copy.deepcopy(pipeline)
        if offset > 0:
            pipeline.append({'$skip': offset})
        if limit > 0:
            pipeline.append({'$limit': limit})
        # pprint.pprint(pipeline)
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def get_triggered_at(self):
        db = self.db
        collection = self.collection
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'triggered_at': {'$last': '$triggered_at'}
                    }
            }, {
                '$sort': {'triggered_at': 1}
            }
        ]
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[-1]['triggered_at']
        return result

    def get_count(self, pipeline):
        db = self.db
        collection = self.collection
        pipeline = copy.deepcopy(pipeline)
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]['triggered_at']
        return result
