#  for db control
from pymongo import MongoClient
import pprint
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


class UEChecker():
    def __init__(self, db, collection, triggered_by):
        self.db = db
        self.collection = collection
        self.triggered_by = triggered_by
        self.triggered_at = self.get_triggered_at()

    def get_triggered_at(self, collection='trigger_log'):
        pipeline = [
            {
                '$match': {'triggered_by': self.triggered_by}
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

    def get_last_records(self, limit=0):
        db = self.db
        collection = self.collection
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
        if limit > 0:
            pipeline.append({'$limit': limit})
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def get_last_records_count(self):
        db = self.db
        collection = self.collection
        triggered_at = self.triggered_at
        pipeline = [
            {
                '$match': {
                    'title': {"$exists": True},
                    'triggered_at': triggered_at
                    }
            }, {
                '$count': 'triggered_at'
                }
        ]
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return next(result)['triggered_at']

    def get_last_errorlogs(self):
        db = self.db
        collection = self.collection
        triggered_at = self.triggered_at
        pipeline = [
            {'$match': {
                'title': {"$exists": False},
                'triggered_at': triggered_at
                }}
        ]
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def check_records(self, records, fields, data_range):
        loop_count = 0
        for record in records:
            if loop_count > data_range:
                break
            pprint.pprint([record[field] for field in fields])
            loop_count += 1


class FPChecker():
    def __init__(self, db, collection, triggered_by):
        self.db = db
        self.collection = collection
        self.triggered_by = triggered_by
        self.triggered_at = self.get_triggered_at()

    def get_triggered_at(self, collection='trigger_log'):
        pipeline = [
            {
                '$match': {'triggered_by': self.triggered_by}
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

    def get_last_records(self, limit=0):
        db = self.db
        collection = self.collection
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
        if limit > 0:
            pipeline.append({'$limit': limit})
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def get_last_records_count(self):
        db = self.db
        collection = self.collection
        triggered_at = self.triggered_at
        pipeline = [
            {
                '$match': {
                    'title': {"$exists": True},
                    'triggered_at': triggered_at
                    }
            }, {
                '$count': 'triggered_at'
                }
        ]
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return next(result)['triggered_at']

    def get_last_errorlogs(self):
        db = self.db
        collection = self.collection
        triggered_at = self.get_triggered_at()
        pipeline = [
            {
                '$match': {
                    'title': {"$exists": False},
                    'triggered_at': triggered_at
                }
            }
        ]
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def check_records(self, records, fields, data_range):
        loop_count = 0
        for record in records:
            if loop_count > data_range:
                break
            pprint.pprint([record[field] for field in fields])
            loop_count += 1
