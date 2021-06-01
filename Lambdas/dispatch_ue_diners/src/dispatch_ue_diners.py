#  for db control
from pymongo import MongoClient, InsertOne

import env


MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)

db = admin_client['ufc']


class UEDinerDispatcher():
    def __init__(self, db, info_collection, offset=False, limit=False):
        self.db = db
        self.collection = info_collection
        self.triggered_at = self.get_triggered_at()
        self.diners_info = self.get_diners_info(info_collection, offset, limit)

    def get_triggered_at(self, collection='trigger_log'):
        pipeline = [
            {
                '$match': {'triggered_by': 'get_ue_list'}
            },
            {
                '$sort': {'triggered_at': 1}
            },
            {
                '$group': {
                    '_id': None,
                    'triggered_at': {'$last': '$triggered_at'}
                    }
            }
        ]
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]['triggered_at']
        return result

    def get_diners_info(self, info_collection, offset=False, limit=False):
        triggered_at = self.triggered_at
        pipeline = [
            {
                '$match': {
                    'title': {"$exists": True},
                    'triggered_at': triggered_at
                }
            }, {
                '$sort': {'uuid': 1}
                }
        ]
        if offset:
            pipeline.append({'$skip': offset})
        if limit:
            pipeline.append({'$limit': limit})
        result = db[info_collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def main(self):
        temp_collection = 'ue_list_temp'
        diners_cursor = self.diners_info
        db[temp_collection].drop()
        records = []
        diners_count = 0
        for diner in diners_cursor:
            record = InsertOne(diner)
            records.append(record)
            diners_count += 1
        db[temp_collection].bulk_write(records)
        return diners_count
