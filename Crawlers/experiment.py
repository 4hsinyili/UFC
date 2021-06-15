import pprint
# import copy
import env
from pymongo import MongoClient, InsertOne, UpdateOne
# import time
from datetime import datetime
# import boto3
# from Crawlers.Trigger_log import TriggerLog
# from Crawlers.AWS_metrics import StatesMetricInfo, LambdaMetricInfo
# import json


MONGO_EC2_URI = env.MONGO_EC2_URI
admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client['ufc']

cursor = db.matched.aggregate([
    {
        "$match": {
            "$or": [
                {'uuid_fp': 'g7ir', 'uuid_ue': '0a62062b-29e9-47de-b82e-febad26a84e4'},
                {'uuid_fp': 'a1ce', 'uuid_ue': '0a5269dd-90f4-4adc-9af1-314e8c33fab9'},
                {'uuid_fp': '', 'uuid_ue': '00b5b8a2-6b10-4ccb-9e8f-3239b07bc41c'},
                {'uuid_fp': '', 'uuid_ue': '009c386d-9361-4d46-9dfa-99027164bcec'},
                {'uuid_fp': 'a03s', 'uuid_ue': ''},
                {'uuid_fp': 'jq5j', 'uuid_ue': '09d27378-b3dc-46d8-8787-f7d7c5cfab34'}
            ]
        }
    },
    {
        "$sort": {"triggered_at": 1}
    },
    {
        "$group": {
            "_id": {"uuid_ue": "$uuid_ue", "uuid_fp": "$uuid_fp"},
            "triggered_at": {"$last": "$triggered_at"},
            "data": {
                "$push": {
                    "uuid_ue": "$uuid_ue",
                    "uuid_fp": "$uuid_fp",
                    "title_ue": "$title_ue",
                    "title_fp": "$title_fp",
                    "triggered_at": "$triggered_at"
                    "image_ue": "$image_ue",
                    "link_ue": "$link_ue",
                    "rating_ue": "$rating_ue",
                    "view_count_ue": "$view_count_ue",
                    "image_fp": "$image_fp",
                    "link_fp": "$link_fp",
                    "rating_fp": "$rating_fp",
                    "view_count_fp": "$view_count_fp",
                    "uuid_gm": "$uuid_gm",
                    "link_gm": "$link_gm",
                    "rating_gm": "$rating_gm",
                    "view_count_gm": "$view_count_gm"
                }
            }
        }
    },
    # {
    #     "$lookup": {
    #         "from": "matched",
    #         "as": "fav",
    #         "let": {
    #             'match_id': '$_id'
    #         },
    #         "pipeline": [
    #             {
    #                 "$match": {
    #                     "$expr": {
    #                         "$eq": ["$_id", "$$match_id"]
    #                     }
    #                 }
    #             },
    #             {
    #                 "$project": {
    #                     "_id": 0,
    #                     "info": {
    #                         # "uuid_ue": "$uuid_ue",
    #                         "title_ue": "$title_ue",
    #                         # "image_ue": "$image_ue",
    #                         # "link_ue": "$link_ue",
    #                         # "rating_ue": "$rating_ue",
    #                         # "view_count_ue": "$view_count_ue",
    #                         # "uuid_fp": "$uuid_fp",
    #                         "title_fp": "$title_fp",
    #                         # "image_fp": "$image_fp",
    #                         # "link_fp": "$link_fp",
    #                         # "rating_fp": "$rating_fp",
    #                         # "view_count_fp": "$view_count_fp",
    #                         # "uuid_gm": "$uuid_gm",
    #                         # "link_gm": "$link_gm",
    #                         # "rating_gm": "$rating_gm",
    #                         # "view_count_gm": "$view_count_gm"
    #                     }
    #                 }
    #             },
    #             {
    #                 "$replaceRoot": {"newRoot": "$info"}
    #             }
    #         ]
    #     }
    # }
])

pprint.pprint(list(cursor))

# update_data = {'field_1': 'value_5', 'field_2': 'value_6', 'field_3': 'value_7'}
# records = [
#     InsertOne(data_1),
#     InsertOne(data_2),
#     UpdateOne({
#             'field_1': 'value_1',
#             'field_2': 'value_2'
#         }, {'$set': update_data})]

# result = db.test.bulk_write(records)
# print(result.bulk_api_result)
# print(result.modified_count)
# print(result.matched_count)

# cursor = db.trigger_log.aggregate(
#     [
#         # {
#         #     "$match": {
#         #         "triggered_at": {
#         #             "$gte": start_time,
#         #             "$lte": end_time
#         #             }
#         #         }
#         # },
#         {
#             "$addFields": {
#                 "insertTime": {
#                     "$toDate": "$_id"
#                     },
#                 "insertMinutes": {
#                     "$minute": {"$toDate": "$_id"}
#                     }
#                 }
#             },
#         {
#             "$group": {
#                 "_id": {
#                     "insertDayOfYear": {
#                         "$dayOfYear": "$insertTime"
#                         },
#                     "insertHour": {
#                         "$hour": "$insertTime"
#                     },
#                     "insertMinutes": {
#                         "$round": [
#                             {"$divide": [
#                                 "$insertMinutes", 10
#                             ]}, 0
#                         ]
#                     },
#                     "triggered_by": "$triggered_by"
#                 },
#                 "data": {
#                     "$addToSet": "$$ROOT"
#                 }
#             }
#         }
#     ]
# )
# data = []
# for record in cursor:
#     pprint.pprint(record)
    # record['log_time'] = record['_id'].generation_time
    # record['log_time'] = record['log_time'].strftime('%Y-%m-%d %H:%M:%S')
    # del record['_id']
    # record['triggered_at'] = record['triggered_at'].strftime('%Y-%m-%d %H:%M:%S')
    # data.append(record)

# pprint.pprint(data)

# print(datetime.datetime.utcnow().timestamp())


# pipeline = [
#     {
#         '$match': {'triggered_by': 'get_ue_list'}
#     },
#     {
#         '$sort': {'triggered_at': 1}
#     },
#     {
#         '$group': {
#             '_id': None,
#             'triggered_at': {'$last': '$triggered_at'},
#             'batch_id': {'$last': '$records_count'}
#             }
#     }
# ]
# cursor = db.trigger_log.aggregate(pipeline=pipeline)
# result = list(result)[0]['triggered_at']
# print(next(cursor))