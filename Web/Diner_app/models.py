# import pprint
import copy
# import time
from django.db import models
from User_app.models import CustomUser
from Crawlers.Trigger_log import TriggerLog
# from Crawlers.AWS_metrics import StatesMetricInfo, LambdaMetricInfo
# Create your models here.


class DashBoardModel():
    def __init__(self, db, cloudwatch):
        self.db = db
        self.cloudwatch = cloudwatch

    def get_data(self, end_time, start_time):
        trigger_log = TriggerLog(self.db)
        # start = time.time()
        trigger_log_data = trigger_log.main(end_time, start_time)
        # stop = time.time()
        result = {
            'trigger_log_data': trigger_log_data,
        }
        return result


class FavoritesManager(models.Manager):
    def update_favorite(self, user, uuid_ue, uuid_fp, activate):
        favorite_sqlrecord = self.update_or_create(
            user=user,
            uuid_ue=uuid_ue,
            uuid_fp=uuid_fp,
            defaults={'activate': activate})
        return favorite_sqlrecord

    def get_favorites(self, user, offset=0):
        if user.id is None:
            return False
        favorite_records = self.filter(user=user, activate=1).order_by('created_at')
        if favorite_records:
            favorites = []
            for i in favorite_records:
                favorites.append((i.uuid_ue, i.uuid_fp))
            return favorites
        else:
            return False


class Favorites(models.Model):
    uuid_ue = models.CharField(max_length=40, default=None, blank=True, null=True)
    uuid_fp = models.CharField(max_length=40, default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activate = models.BooleanField(default=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    objects = models.Manager()
    manager = FavoritesManager()

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user'])
            ]

    def __str__(self):
        return f'user: {self.user.email} likes {self.uuid_ue} ,{self.uuid_fp} == {self.activate}'


class MatchChecker():
    def __init__(self, db, collection, triggered_by):
        self.db = db
        self.collection = collection
        self.triggered_by = triggered_by
        self.triggered_at = self.get_triggered_at()

    def get_triggered_at(self, collection='trigger_log'):
        db = self.db
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
            },
            {
                "$limit": 1
            }
        ]
        cursor = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        result = next(cursor)['triggered_at']
        cursor.close()
        return result


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
            {"$unwind": "$tags_fp"},
            {
                '$group': {
                    '_id': None,
                    'tags_ue': {'$addToSet': '$tags_ue'},
                    'tags_fp': {'$addToSet': '$tags_fp'},
                    }
            }, {
                '$project': {'_id': 0}
            }
        ]
        cursor = db[collection].aggregate(pipeline=pipeline)
        filters = next(cursor)
        cursor.close()
        return filters


class MatchSearcher():
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection

    def get_search_result(self, condition, triggered_at, offset=0, user=False):
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
        pipeline = [condition for condition in conditions if condition != {}]
        project_stage = {
            '$project': {
                '_id': 0,
                'menu_ue': 0,
                'menu_fp': 0,
                'item_pair_ue': 0,
                'cheaper_ue': 0,
                'item_pair_fp': 0,
                'cheaper_fp': 0
            }
        }
        pipeline.append(project_stage)
        facet_stage = {
            "$facet": {
                "data": [
                    {"$skip": offset},
                    {"$limit": 12}
                ],
                "count": [
                    {"$count": "uuid_ue"}
                ]
            }
        }
        pipeline.append(facet_stage)
        # print("====================================================")
        # print("now is using UESearcher's get_search_result function")
        # print("below is the pipeline")
        # pprint.pprint(pipeline)
        # start = time.time()
        cursor = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        raw = next(cursor)
        raw_diners = raw['data']
        raw_count = raw['count']
        result_count = raw_count[0]['uuid_ue']
        if user:
            favorites = Favorites.manager.get_favorites(user)
        else:
            favorites = False
        diners = []
        if favorites:
            favorites_ue = [i[0] for i in favorites if i[0] != '']
            favorites_fp = [i[1] for i in favorites if i[1] != '']
            for diner in raw_diners:
                if (diner['uuid_ue'] in favorites_ue) or (diner['uuid_fp'] in favorites_fp):
                    diner['favorite'] = True
                    diners.append(diner)
                else:
                    diner['favorite'] = False
                    diners.append(diner)
        else:
            for diner in raw_diners:
                diner['favorite'] = False
                diners.append(diner)
        cursor.close()
        # stop = time.time()
        # print('mongodb query took: ', stop - start, 's.')
        return diners, result_count

    def get_count(self, db, collection, pipeline):
        db = self.db
        collection = self.collection
        count_pipeline = copy.deepcopy(pipeline)
        count_pipeline.extend([
            {'$count': 'triggered_at'}
        ])
        cursor = db[collection].aggregate(pipeline=count_pipeline, allowDiskUse=True)
        result = list(cursor)
        cursor.close()
        if len(result) > 0:
            diners_count = result[0]['triggered_at']
        else:
            diners_count = 0
        return diners_count

    def get_random(self, triggered_at, user=False):
        db = self.db
        collection = self.collection
        pipeline = [
            {"$match": {"triggered_at": triggered_at}},
            {"$sample": {"size": 6}}
        ]
        cursor = db[collection].aggregate(pipeline)
        if user:
            favorites = Favorites.manager.get_favorites(user)
        else:
            favorites = False
        diners = []
        if favorites:
            for diner in cursor:
                if (diner['uuid_ue'] in favorites) or (diner['uuid_fp'] in favorites):
                    diner['favorite'] = True
                    diners.append(diner)
                else:
                    diner['favorite'] = False
                    diners.append(diner)
        else:
            for diner in cursor:
                diner['favorite'] = False
                diners.append(diner)
        cursor.close()
        return diners


class MatchDinerInfo():
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection

    def get_diner(self, uuid_ue, uuid_fp, user=False):
        db = self.db
        collection = self.collection
        pipeline = [
            {
                "$match": {
                    "uuid_ue": uuid_ue,
                    "uuid_fp": uuid_fp
                }
            },
            {
                "$sort": {"triggered_at": -1}
            },
            {
                '$limit': 1
            }
        ]
        # print("====================================================")
        # print("now is using UEDinerInfo's get_diner function")
        # print("below is the pipeline")
        # pprint.pprint(pipeline)
        # start = time.time()
        cursor = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        # stop = time.time()
        # print('mongodb query took: ', stop - start, 's.')
        if user:
            favorites = Favorites.manager.get_favorites(user)
        else:
            favorites = False
        try:
            diner = next(cursor)
            if favorites:
                if (diner['uuid_ue'] in favorites) or (diner['uuid_fp'] in favorites):
                    diner['favorite'] = True
                else:
                    diner['favorite'] = False
            else:
                diner['favorite'] = False
        except Exception:
            return False
        cursor.close()
        return diner
