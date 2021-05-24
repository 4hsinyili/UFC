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


class UFFilters():
    def __init__(self, db, collection, triggered_at):
        self.db = db
        self.collection = collection
        self.triggered_at = triggered_at

    def get_filters(self):
        db = db = self.db
        collection = self.collection
        triggered_at = self.triggered_at
        rating = self.get_ratings(db, collection, triggered_at)
        rating['rating'].sort()
        tags = self.get_tags(db, collection, triggered_at)
        deliver_fee = self.get_deliver_fee(db, collection, triggered_at)
        deliver_time = self.get_deliver_time(db, collection, triggered_at)
        deliver_time['deliver_time'] = [i for i in deliver_time['deliver_time'] if type(i) == int]
        deliver_time['deliver_time'].sort()
        budget = self.get_budget(db, collection, triggered_at)
        budget['budget'].sort()
        view_count = self.get_view_count(db, collection, triggered_at)
        view_count['view_count'] = [i for i in view_count['view_count'] if i]
        view_count['view_count'].sort()
        open_days = ['Mon.', 'Tue.', 'Wed.', 'Thu.', 'Fri.', 'Sat.', 'Sun.']
        result = {**rating, **tags, **deliver_fee, **deliver_time, **budget, **view_count, 'open_days': open_days}
        return result

    def get_ratings(self, db, collection, triggered_at):
        pipeline = [
            {"$match": {"triggered_at": triggered_at}},
            {
                '$group': {
                    '_id': None,
                    'rating': {'$addToSet': '$rating'}
                    }
            }, {
                '$project': {'_id': 0, 'rating': 1}
            }
        ]
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]
        return result

    def get_tags(self, db, collection, triggered_at):
        pipeline = [
            {"$match": {"triggered_at": triggered_at}},
            {
                '$project': {'_id': 0, 'tags': 1}
            }, {
                '$unwind': '$tags'
            }, {
                '$group': {
                    '_id': None,
                    'tags': {'$addToSet': '$tags'}
                    }
            }, {
                '$project': {'_id': 0, 'tags': 1}
            }
        ]
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]
        return result

    def get_deliver_fee(self, db, collection, triggered_at):
        pipeline = [
            {"$match": {"triggered_at": triggered_at}},
            {
                '$group': {
                    '_id': None,
                    'deliver_fee': {'$addToSet': '$deliver_fee'}
                    }
            }, {
                '$project': {'_id': 0, 'deliver_fee': 1}
            }
        ]
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]
        return result

    def get_deliver_time(self, db, collection, triggered_at):
        pipeline = [
            {"$match": {"triggered_at": triggered_at}},
            {
                '$group': {
                    '_id': None,
                    'deliver_time': {'$addToSet': '$deliver_time'}
                    }
            }, {
                '$project': {'_id': 0, 'deliver_time': 1}
            }
        ]
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]
        return result

    def get_budget(self, db, collection, triggered_at):
        pipeline = [
            {"$match": {"triggered_at": triggered_at}},
            {
                '$group': {
                    '_id': None,
                    'budget': {'$addToSet': '$budget'}
                    }
            }, {
                '$project': {'_id': 0, 'budget': 1}
            }
        ]
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]
        return result

    def get_view_count(self, db, collection, triggered_at):
        pipeline = [
            {"$match": {"triggered_at": triggered_at}},
            {
                '$group': {
                    '_id': None,
                    'view_count': {'$addToSet': {'$round': ['$view_count', -2]}}
                    }
            }, {
                '$project': {'_id': 0, 'view_count': 1}
            }
        ]
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]
        return result

