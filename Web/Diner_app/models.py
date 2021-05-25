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

    def get_latest_records(self, pipeline, db='', collection='', offset=0, limit=0):
        if db == '':
            db = self.db
        if collection == '':
            collection = self.collection
        pipeline = copy.deepcopy(pipeline)
        if offset > 0:
            pipeline.append({'$skip': offset})
        if limit > 0:
            pipeline.append({'$limit': limit})
        print("====================================================")
        print("now is using UEChecker's get_latest_records function")
        print("below is the pipeline")
        pprint.pprint(pipeline)
        start = time.time()
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        stop = time.time()
        print('mongodb query took: ', stop - start, 's.')
        return result

    def get_count(self, pipeline):
        db = self.db
        collection = self.collection
        pipeline = copy.deepcopy(pipeline)
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]['triggered_at']
        return result
    
    def get_triggered_at(self, db='', collection=''):
        if db == '':
            db = self.db
        if collection == '':
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


class UEFilters():
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection

    def get_filters(self, triggered_at):
        db = db = self.db
        collection = self.collection
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


class UESearcher():
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection

    def get_search_result(self, condition, triggered_at, offset=0):
        db = self.db
        collection = self.collection
        match_conditions = {"$match": {
            "triggered_at": triggered_at,
            'title': {'$exists': True}
            }}
        sort_condttions = {}
        conditions = [match_conditions, sort_condttions]
        try:
            for match in condition['keyword']:
                match_conditions['$match'][match['field']] = {'$regex': match['value']}
        except Exception:
            pass
        try:
            for filter in condition['filter']:
                if filter['field'] not in ['tags', 'open_days']:
                    match_conditions['$match'][filter['field']] = {filter['filter']: filter['value']}
                else:
                    match_conditions['$match'][filter['field']] = {
                        '$elemMatch': {'$eq': filter['value']}
                        }
        except Exception:
            pass
        try:
            sort_condttions = {'$sort': {}}
            for sorter in condition['sorter']:
                sort_condttions['$sort'][sorter['field']] = sorter['sorter']
        except Exception:
            pass
        pipeline = [condition for condition in conditions if condition != {}]
        result_count = self.get_count(db, collection, pipeline)
        pprint.pprint(result_count)
        if offset > 0:
            pipeline.append({'$skip': offset})
        limit = {'$limit': 6}
        pipeline.append(limit)
        print("====================================================")
        print("now is using UESearcher's get_search_result function")
        print("below is the pipeline")
        pprint.pprint(pipeline)
        start = time.time()
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        stop = time.time()
        print('mongodb query took: ', stop - start, 's.')
        return result, result_count

    def get_count(self, db, collection, pipeline):
        db = self.db
        collection = self.collection
        count_pipeline = copy.deepcopy(pipeline)
        count_pipeline.extend([
            {'$group': {
                '_id': {
                    'title': '$title',
                },
                'triggered_at': {'$last': '$triggered_at'}
            }},
            {'$count': 'triggered_at'}
        ])
        pprint.pprint(count_pipeline)
        result = db[collection].aggregate(pipeline=count_pipeline)
        result = list(result)
        if len(result) > 0:
            diners_count = result[0]['triggered_at']
        else:
            diners_count = 0
        return diners_count


class UEDinerInfo():
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection

    def get_diner(self, diner_id, triggered_at):
        db = self.db
        collection = self.collection
        match_conditions = {
            "$match": {
                "triggered_at": triggered_at,
                "uuid": diner_id
                }}
        limit = {'$limit': 1}
        conditions = [match_conditions, limit]
        pipeline = [condition for condition in conditions if condition != {}]
        print("====================================================")
        print("now is using UEDinerInfo's get_diner function")
        print("below is the pipeline")
        pprint.pprint(pipeline)
        start = time.time()
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        stop = time.time()
        print('mongodb query took: ', stop - start, 's.')
        return result


class Pipeline():
    ue_list_pipeline = [
        {'$sort': {'triggered_at': -1, 'uuid': 1}},
        {'$match': {'title': {'$exists': True}}},
        {'$group': {
            '_id': {
                'title': '$title',
                'link': '$link',
                'deliver_fee': '$deliver_fee',
                'deliver_time': '$deliver_time',
                'budget': '$budget',
                'uuid': '$uuid',
                'triggered_at': '$triggered_at',
                'menu': '$menu',
                'budget': '$budget',
                'rating': '$rating',
                'view_count': '$view_count',
                'image': '$image',
                'tags': '$tags',
                'address': '$address',
                'gps': '$gps',
                'open_hours': '$open_hours',
                'UE_choice': '$UE_choice'
            },
            'triggered_at': {'$last': '$triggered_at'}
        }},
        {'$sort': {'_id.uuid': 1}}
    ]
    ue_count_pipeline = [
        {'$sort': {'triggered_at': -1, 'uuid': 1}},
        {'$match': {'title': {'$exists': True}}},
        {'$group': {
            '_id': {
                'title': '$title',
            },
            'triggered_at': {'$last': '$triggered_at'}
        }},
        {'$count': 'triggered_at'}
    ]
