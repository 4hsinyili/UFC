# for db control
from pymongo import MongoClient

# home-made module
# for file handling
import env

# my utility belt
import utils

# module need to test
from Diner_app.mongo_query import SearcherQuery, DinerInfoQuery, FiltersQuery


def get_search_result(db, collection, condition, triggered_at, offset):
    search_waiter = SearcherQuery(db, collection)
    result, result_count = search_waiter.get_search_result(condition, triggered_at, offset)
    return result, result_count


def test_get_search_result():
    MONGO_EC2_URI = env.MONGO_EC2_URI
    admin_client = MongoClient(MONGO_EC2_URI)
    db = admin_client['ufc_test']
    collection = 'test'
    condition = {
        "filter": [{
            "field": "default",
            "filter": "default",
            "value": None
        }, {
            "field": "rating_ue",
            "filter": "$lte",
            "value": 4.6
        }],
        "sorter": [{
            "field": "default",
            "sorter": None
        }]
    }
    offset = 0
    triggered_at = "2021-06-17T08:00:00Z"
    result, result_count = get_search_result(db, collection, condition, triggered_at, offset)
    assert result_count == 5


def get_diner(db, collection, uuid_ue, uuid_fp):
    diner_info_waiter = DinerInfoQuery(db, collection)
    diner = diner_info_waiter.get_diner(uuid_ue, uuid_fp)
    del diner['_id']
    return diner


def test_get_diner():
    MONGO_EC2_URI = env.MONGO_EC2_URI
    admin_client = MongoClient(MONGO_EC2_URI)
    db = admin_client['ufc_test']
    collection = 'test'
    uuid_ue = "08dba44e-afca-41c5-b795-74ecf0221876"
    uuid_fp = ''
    diner_should_found = utils.read_json('/Users/4hsinyili/Documents/GitHub/UFC/Test/diner_should_found.json')
    assert get_diner(db, collection, uuid_ue, uuid_fp) == diner_should_found


def get_filters(db, collection, triggered_at):
    filters_waiter = FiltersQuery(db, collection)
    filters = filters_waiter.get_filters(triggered_at)
    return filters


def test_get_filters():
    MONGO_EC2_URI = env.MONGO_EC2_URI
    admin_client = MongoClient(MONGO_EC2_URI)
    db = admin_client['ufc_test']
    collection = 'test'
    diner_list = utils.read_json('/Users/4hsinyili/Documents/GitHub/UFC/Test/diner_list.json')
    triggered_at = "2021-06-17T08:00:00Z"
    filters_should_found_ue = []
    filters_should_found_fp = []
    for diner in diner_list:
        if diner['tags_ue'] != []:
            filters_should_found_ue.extend(diner['tags_ue'])
        if diner['tags_fp'] != []:
            filters_should_found_fp.extend(diner['tags_fp'])
    filters_should_found_ue = set(filters_should_found_ue)
    filters_should_found_fp = set(filters_should_found_fp)

    filters_found = get_filters(db, collection, triggered_at)
    filters_found_ue = set(filters_found['tags_ue'])
    filters_found_fp = set(filters_found['tags_fp'])
    assert (filters_should_found_ue == filters_found_ue) and (filters_should_found_fp == filters_found_fp)
