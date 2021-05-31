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


class MatchChecker():
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
        result = next(result)['triggered_at']
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


class MatchFilters():
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection

    def get_filters(self, triggered_at):
        db = db = self.db
        collection = self.collection
        pipeline = [
            {"$match": {"triggered_at": triggered_at}},
            {"$unwind": "$tags_ue"},
            {"$unwind": "$open_days_ue"},
            {"$unwind": "$tags_fp"},
            {"$unwind": "$open_days_fp"},
            {
                '$group': {
                    '_id': None,
                    'rating_ue': {'$addToSet': '$rating_ue'},
                    'deliver_fee_ue': {'$addToSet': '$deliver_fee_ue'},
                    'deliver_time_ue': {'$addToSet': '$deliver_time_ue'},
                    'budget_ue': {'$addToSet': '$budget_ue'},
                    'view_count_ue': {'$addToSet': {'$round': ['$view_count_ue', -2]}},
                    'tags_ue': {'$addToSet': '$tags_ue'},
                    'open_days_ue': {'$addToSet': '$open_days_ue'},
                    'rating_fp': {'$addToSet': '$rating_fp'},
                    'deliver_fee_fp': {'$addToSet': '$deliver_fee_fp'},
                    'deliver_time_fp': {'$addToSet': '$deliver_time_fp'},
                    'budget_fp': {'$addToSet': '$budget_fp'},
                    'view_count_fp': {'$addToSet': {'$round': ['$view_count_fp', -2]}},
                    'tags_fp': {'$addToSet': '$tags_fp'},
                    'open_days_fp': {'$addToSet': '$open_days_fp'},
                    }
            }, {
                '$project': {'_id': 0}
            }
        ]
        filters = next(db[collection].aggregate(pipeline=pipeline))
        filters['open_days_fp'] = [i for i in filters['open_days_fp'] if type(i) == int]
        need_sorts = ['rating_ue', 'deliver_time_ue', 'budget_ue', 'view_count_ue', 'open_days_ue', 'rating_fp', 'deliver_time_fp', 'budget_fp', 'view_count_fp', 'open_days_fp']
        for need_sort in need_sorts:
            filters[need_sort].sort()
        return filters


class MatchSearcher():
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection

    def get_search_result(self, condition, triggered_at, offset=0):
        db = self.db
        collection = self.collection
        match_condition = {
            "$match": {
                "triggered_at": triggered_at
            }}
        conditions = [match_condition]
        try:
            keyword = condition['keyword']
            keyword_condition = {
                "$match": {
                    "$or": []
                }
            }
            keyword_condition['$match']["$or"] = [
                {"title_ue": {'$regex': keyword}},
                {"title_fp": {'$regex': keyword}},
                {"tags_ue": {"$elemMatch": {'$regex': keyword}}},
                {"tags_ue": {"$elemMatch": {'$regex': keyword}}}
                ]
            conditions.insert(0, keyword_condition)
        except Exception:
            pass
        try:
            for filter in condition['filter']:
                if (filter['filter'] is None) or (filter['value'] is None):
                    continue
                elif filter['field'] not in ['tags', 'open_days']:
                    match_condition['$match'][filter['field']] = {filter['filter']: filter['value']}
                else:
                    match_condition['$match'][filter['field']] = {
                        '$elemMatch': {'$eq': filter['value']}
                        }
        except Exception:
            pass
        try:
            sort_conditions = {"$sort": {}}
            for sorter in condition['sorter']:
                if (sorter == {}) or (sorter['field'] is None) or (sorter['sorter'] is None):
                    continue
                sort_conditions['$sort'][sorter['field']] = sorter['sorter']
            if sort_conditions != {"$sort": {}}:
                conditions.append(sort_conditions)
        except Exception:
            pass
        pprint.pprint(conditions)
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
            {'$count': 'triggered_at'}
        ])
        result = db[collection].aggregate(pipeline=count_pipeline)
        result = list(result)
        if len(result) > 0:
            diners_count = result[0]['triggered_at']
        else:
            diners_count = 0
        return diners_count
    
    def get_random(self, triggered_at):
        db = self.db
        collection = self.collection
        pipeline = [
            {"$match": {"triggered_at": triggered_at}},
            {"$sample": {"size": 6}}
        ]
        result = db[collection].aggregate(pipeline, allowDiskUse=True)
        return result
        


class MatchDinerInfo():
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection

    def get_diner(self, diner_id, source, triggered_at):
        db = self.db
        collection = self.collection
        match_conditions = {
            "$match": {
                "triggered_at": triggered_at,
                f"uuid_{source}": diner_id
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
