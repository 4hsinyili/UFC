#  for db control
from pymongo import MongoClient

# for file handling
import env
import conf
import utils

MONGO_EC2_URI = env.MONGO_EC2_URI

DB_NAME = conf.DB_NAME
LIST_COLLECTION = conf.FP_LIST_COLLECTION
LIST_TEMP_COLLECTION = conf.FP_LIST_TEMP_COLLECTION
LOG_COLLECTION = conf.LOG_COLLECTION
GET_FP_LIST = conf.GET_FP_LIST
admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client[DB_NAME]


def lambda_handler(event, context):
    dispatcher = utils.DinerDispatcher(db,
                                       read_collection=LIST_COLLECTION,
                                       write_collection=LIST_TEMP_COLLECTION,
                                       log_collection=LOG_COLLECTION,
                                       r_triggered_by=GET_FP_LIST)
    diners_count = dispatcher.main()

    indexes = utils.dispatch_diners_lambda(diners_count)

    return indexes
