# for db control
from pymongo import MongoClient

# home-made module
# for file handling
import env
import conf

# my utility belt
import utils


API_KEY = env.PLACE_API_KEY
MONGO_EC2_URI = env.MONGO_EC2_URI

DB_NAME = conf.DB_NAME
MATCHED_COLLECTION = conf.MATCHED_COLLECTION
STEPFUNCTION_LOG_COLLECTION = conf.STEPFUNCTION_LOG_COLLECTION
LOG_COLLECTION = conf.LOG_COLLECTION

MATCH = conf.MATCH
PLACE = conf.PLACE

admin_client = MongoClient(MONGO_EC2_URI)
admin_client.drop_database('ufc_test')
db_test = admin_client['ufc_test']

diner_list = utils.read_json('/Users/4hsinyili/Documents/GitHub/UFC/Test/diner_list.json')
db_test.test.insert_many(diner_list)
