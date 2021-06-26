from Diner_app.models import Favorites
from collections import defaultdict


class DashBoardQuery():
    def __init__(self, db, log_collection, triggered_by_list):
        self.db = db
        self.log_collection = log_collection
        self.triggered_by_list = triggered_by_list

    def get_log(self, end_time, start_time):
        db = self.db
        log_collection = self.log_collection
        cursor = db[log_collection].aggregate([{
            "$match": {
                "triggered_at": {
                    "$gte": start_time,
                    "$lte": end_time
                },
                "batch_id": {
                    "$exists": True
                }
            },
        }, {
            "$group": {
                "_id": {
                    "batch_id": "$batch_id",
                    "triggered_by": "$triggered_by"
                },
                "data": {
                    "$push": "$$ROOT"
                }
            }
        }])
        data = []
        for record in cursor:
            key = {
                "triggered_by": record['_id']['triggered_by'],
                "batch_id": record['_id']['batch_id']
            }
            result = (key, record['data'])
            data.append(result)
        cursor.close()
        # pprint.pprint(data)
        return data

    def parse_data(self, data, trigered_by):
        result = defaultdict(dict)
        for bucket in data:
            key = bucket[0]
            if key['triggered_by'] == trigered_by:
                bucket_val = bucket[1]
                for val in bucket_val:
                    val['log_time'] = val['_id'].generation_time
                    val['log_time'] = val['log_time'].strftime(
                        '%Y-%m-%d %H:%M:%S')
                    del val['_id']
                    val['triggered_at'] = val['triggered_at'].strftime(
                        '%Y-%m-%d %H:%M:%S')
                result[key['triggered_by']][key['batch_id']] = bucket_val
        if result == []:
            return False
        return result

    def main(self, end_time, start_time):
        data = self.get_log(end_time, start_time)
        triggered_by_list = self.triggered_by_list
        result = {}
        for triggered_by in triggered_by_list:
            result.update(self.parse_data(data, triggered_by))
        # return data
        return result


class FiltersQuery():
    def __init__(self, db, read_collection):
        self.db = db
        self.read_collection = read_collection

    def get_filters(self, triggered_at):
        db = self.db
        read_collection = self.read_collection
        pipeline = [{
            "$match": {
                "triggered_at": triggered_at
            }
        }, {
            "$unwind": {
                "path": "$tags_ue",
                "preserveNullAndEmptyArrays": True
            }
        }, {
            "$unwind": {
                "path": "$tags_fp",
                "preserveNullAndEmptyArrays": True
            }
        }, {
            '$group': {
                '_id': None,
                'tags_ue': {
                    '$addToSet': '$tags_ue'
                },
                'tags_fp': {
                    '$addToSet': '$tags_fp'
                },
            }
        }, {
            '$project': {
                '_id': 0
            }
        }]
        cursor = db[read_collection].aggregate(pipeline=pipeline)
        filters = next(cursor)
        cursor.close()
        return filters


class SearcherQuery():
    def __init__(self, db, read_collection, limit):
        self.db = db
        self.read_collection = read_collection
        self.limit = limit

    def assemble_condition(self, condition, triggered_at):
        match_condition = {"$match": {"triggered_at": triggered_at}}
        conditions = [match_condition]
        try:
            keyword = condition['keyword']
            keyword_condition = {"$match": {"$or": []}}
            keyword_condition['$match']["$or"] = [{
                "title_ue": {
                    '$regex': keyword
                }
            }, {
                "title_fp": {
                    '$regex': keyword
                }
            }, {
                "tags_ue": {
                    "$elemMatch": {
                        '$regex': keyword
                    }
                }
            }, {
                "tags_ue": {
                    "$elemMatch": {
                        '$regex': keyword
                    }
                }
            }]
            conditions.insert(0, keyword_condition)
        except Exception:
            pass
        try:
            for filter in condition['filter']:
                if (filter['filter'] is None) or (filter['value'] is None):
                    continue
                elif filter['field'] not in ['tags_ue', 'open_days_ue', 'tags_fp', 'open_days_fp']:
                    match_condition['$match'][filter['field']] = {
                        filter['filter']: filter['value']
                    }
                    if filter['filter'] == '$lte':
                        match_condition['$match'][filter['field']].update(
                            {'$gt': 0})
                    elif filter['field'] == 'choice_fp':
                        match_condition['$match']['uuid_fp'] = {'$ne': ""}
                    elif filter['field'] == 'choice_ue':
                        match_condition['$match']['uuid_ue'] = {'$ne': ""}
                else:
                    match_condition['$match'][filter['field']] = {
                        '$elemMatch': {
                            '$eq': filter['value']
                        }
                    }
        except Exception:
            pass
        try:
            sort_conditions = {"$sort": {}}
            for sorter in condition['sorter']:
                if (sorter == {}) or (sorter['field'] is
                                      None) or (sorter['sorter'] is None):
                    continue
                sort_conditions['$sort'][sorter['field']] = sorter['sorter']
                if sorter['field'].endswith('_ue'):
                    match_condition['$match']['uuid_ue'] = {'$ne': ""}
                elif sorter['field'].endswith('_fp'):
                    match_condition['$match']['uuid_fp'] = {'$ne': ""}
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
        return pipeline

    def assemble_search_pipeline(self, pipeline, offset):
        facet_stage = {
            "$facet": {
                "data": [{
                    "$skip": offset
                }, {
                    "$limit": self.limit
                }],
                "count": [{
                    "$count": "uuid_ue"
                }]
            }
        }
        pipeline.append(facet_stage)
        return pipeline

    def assemble_shuffle_pipeline(self, condition, pipeline):
        sort_conditions = {"$sort": {}}
        try:
            sort_conditions = {"$sort": {}}
            for sorter in condition['sorter']:
                if (sorter == {}) or (sorter['field'] is
                                      None) or (sorter['sorter'] is None):
                    continue
                sort_conditions['$sort'][sorter['field']] = sorter['sorter']
        except Exception:
            pass
        facet_stage = {
            "$facet": {
                "data": [
                    {
                        "$sample": {
                            "size": self.limit
                        }
                    }
                ],
                "count": [
                    {
                        "$count": "uuid_ue"
                    }
                ]
            }
        }
        if sort_conditions == {"$sort": {}}:
            pipeline.append(facet_stage)
            return pipeline
        else:
            facet_stage["$facet"]["data"].append(sort_conditions)
            pipeline.append(facet_stage)
            return pipeline

    def get_user_favorites(self, user):
        if user:
            favorites = Favorites.manager.get_favorites(user)
        else:
            favorites = False
        return favorites

    def check_whether_favorite(self, raw_diners, user):
        favorites = self.get_user_favorites(user)
        diners = []
        if favorites:
            favorites_ue = [i[0] for i in favorites if i[0] != '']
            favorites_fp = [i[1] for i in favorites if i[1] != '']
            for diner in raw_diners:
                if (diner['uuid_ue'] in favorites_ue) or (diner['uuid_fp']
                                                          in favorites_fp):
                    diner['favorite'] = True
                    diners.append(diner)
                else:
                    diner['favorite'] = False
                    diners.append(diner)
        else:
            for diner in raw_diners:
                diner['favorite'] = False
                diners.append(diner)
        return diners

    def get_search_result(self, condition, triggered_at, offset=0, user=False):
        db = self.db
        read_collection = self.read_collection
        pipeline = self.assemble_condition(condition, triggered_at)
        pipeline = self.assemble_search_pipeline(pipeline, offset)
        # print("====================================================")
        # print("now is using SearcherQuery's get_search_result function")
        # print("below is the pipeline")
        # pprint.pprint(pipeline)
        # start = time.time(
        cursor = db[read_collection].aggregate(pipeline=pipeline,
                                               allowDiskUse=True)
        raw = next(cursor)
        raw_diners = raw['data']
        raw_count = raw['count']
        if len(raw_count) == 0:
            return False, False
        result_count = raw_count[0]['uuid_ue']
        diners = self.check_whether_favorite(raw_diners, user)
        cursor.close()
        # stop = time.time()
        # print('mongodb query took: ', stop - start, 's.')
        return diners, result_count

    def get_random(self, condition, triggered_at, user=False):
        db = self.db
        read_collection = self.read_collection
        pipeline = self.assemble_condition(condition, triggered_at)
        pipeline = self.assemble_shuffle_pipeline(condition, pipeline)
        cursor = db[read_collection].aggregate(pipeline)
        raw = next(cursor)
        raw_diners = raw['data']
        raw_count = raw['count']
        if len(raw_count) == 0:
            return False
        diners = self.check_whether_favorite(raw_diners, user)
        cursor.close()
        return diners, self.limit


class DinerInfoQuery():
    def __init__(self, db, read_collection):
        self.db = db
        self.read_collection = read_collection

    def get_diner(self, uuid_ue, uuid_fp, user=False):
        db = self.db
        read_collection = self.read_collection
        pipeline = [{
            "$match": {
                "uuid_ue": uuid_ue,
                "uuid_fp": uuid_fp
            }
        }, {
            "$sort": {
                "triggered_at": -1
            }
        }, {
            '$limit': 1
        }]
        # print("====================================================")
        # print("now is using UEDinerInfo's get_diner function")
        # print("below is the pipeline")
        # pprint.pprint(pipeline)
        # start = time.time()
        cursor = db[read_collection].aggregate(pipeline=pipeline,
                                               allowDiskUse=True)
        # stop = time.time()
        # print('mongodb query took: ', stop - start, 's.')
        diner = next(cursor)
        if user:
            favorites = Favorites.manager.check_favorite(
                user, diner['uuid_ue'], diner['uuid_fp'])
        else:
            favorites = False
        if favorites:
            diner['favorite'] = True
        else:
            diner['favorite'] = False
        cursor.close()
        return diner


class FavoritesQuery():
    def __init__(self, db, read_collection):
        self.db = db
        self.read_collection = read_collection

    def get_favorites_diners(self, user, offset):
        db = self.db
        favorites = Favorites.manager.get_favorites(user, offset, 6)
        if not favorites:
            return False
        diners = []
        or_conditions = []
        for favorite in favorites:
            uuid_ue = favorite[0]
            uuid_fp = favorite[1]
            match = {"uuid_ue": uuid_ue, "uuid_fp": uuid_fp}
            or_conditions.append(match)
        match_condition = [{
            "$match": {
                "$or": or_conditions
            }
        }, {
            "$sort": {
                "triggered_at": 1
            }
        }, {
            "$group": {
                "_id": {
                    "uuid_ue": "$uuid_ue",
                    "uuid_fp": "$uuid_fp"
                },
                "triggered_at": {
                    "$last": "$triggered_at"
                },
                "data": {
                    "$push": {
                        "uuid_ue": "$uuid_ue",
                        "uuid_fp": "$uuid_fp",
                        "title_ue": "$title_ue",
                        "title_fp": "$title_fp",
                        "triggered_at": "$triggered_at",
                        "image_ue": "$image_ue",
                        "link_ue": "$link_ue",
                        "rating_ue": "$rating_ue",
                        "view_count_ue": "$view_count_ue",
                        "tags_ue": "$tags_ue",
                        "deliver_fee_ue": "$deliver_fee_ue",
                        "deliver_time_ue": "$deliver_time_ue",
                        "image_fp": "$image_fp",
                        "link_fp": "$link_fp",
                        "rating_fp": "$rating_fp",
                        "view_count_fp": "$view_count_fp",
                        "tags_fp": "$tags_fp",
                        "deliver_fee_fp": "$deliver_fee_fp",
                        "deliver_time_fp": "$deliver_time_fp",
                        "uuid_gm": "$uuid_gm",
                        "link_gm": "$link_gm",
                        "rating_gm": "$rating_gm",
                        "view_count_gm": "$view_count_gm"
                    }
                }
            }
        }]
        diners = list(db['matched'].aggregate(match_condition))
        if len(diners) == 0:
            return False
        result = {}
        for diner_dict in diners:
            diner = diner_dict['data'][-1]
            diner['favorite'] = True
            key = (diner['uuid_ue'], diner['uuid_fp'])
            result[key] = diner
        results = []
        for favorite in favorites:
            uuid_ue = favorite[0]
            uuid_fp = favorite[1]
            sort_key = (uuid_ue, uuid_fp)
            results.append(result[sort_key])
        return results
