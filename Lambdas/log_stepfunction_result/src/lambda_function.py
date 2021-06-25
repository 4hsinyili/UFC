#  for db control
from pymongo import MongoClient

# for file handling
import env
import conf
import utils

MONGO_EC2_URI = env.MONGO_EC2_URI
DRIVER_PATH = env.DRIVER_PATH
DB_NAME = conf.DB_NAME

UE_DETAIL_COLLECTION = conf.UE_DETAIL_COLLECTION
FP_DETAIL_COLLECTION = conf.FP_DETAIL_COLLECTION
MATCHED_COLLECTION = conf.MATCHED_COLLECTION

LOG_COLLECTION = conf.LOG_COLLECTION
GET_UE_DETAIL = conf.GET_UE_DETAIL
GET_FP_DETAIL = conf.GET_FP_DETAIL

admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client[DB_NAME]


def lambda_handler(event, context):
    uechecker = utils.Checker(db,
                              read_collection=UE_DETAIL_COLLECTION,
                              log_collection=LOG_COLLECTION,
                              r_triggered_by=GET_UE_DETAIL)
    fpchecker = utils.Checker(db,
                              read_collection=FP_DETAIL_COLLECTION,
                              log_collection=LOG_COLLECTION,
                              r_triggered_by=GET_FP_DETAIL)

    ue_triggered_at = uechecker.triggered_at
    fp_triggered_at = fpchecker.triggered_at

    ue_detail_count = uechecker.get_latest_records_count()
    fp_detail_count = fpchecker.get_latest_records_count()

    print('There are ', ue_detail_count, ' diners in ue_detail triggered_at',
          ue_triggered_at)
    print('There are ', fp_detail_count, ' diners in fp_detail triggered_at',
          fp_triggered_at)

    collection = 'stepfunction_log'

    record = {
        'ue_triggered_at': ue_triggered_at,
        'ue_detail_count': ue_detail_count,
        'fp_triggered_at': fp_triggered_at,
        'fp_detail_count': fp_detail_count,
        'matched': False
    }

    db[collection].insert_one(record)

    result = {
        'ue_triggered_at': str(ue_triggered_at),
        'ue_detail_count': ue_detail_count,
        'fp_triggered_at': str(fp_triggered_at),
        'fp_detail_count': fp_detail_count,
    }

    return result
