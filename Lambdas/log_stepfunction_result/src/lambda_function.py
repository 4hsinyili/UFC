#  for db control
from pymongo import MongoClient

# for file handling
import env

from log_stepfunction_result import UEChecker, FPChecker

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc']


def lambda_handler(event, context):
    uechecker = UEChecker(db, 'ue_detail', 'get_ue_detail')
    fpchecker = FPChecker(db, 'fp_detail', 'get_fp_detail')

    ue_triggered_at = uechecker.triggered_at
    fp_triggered_at = fpchecker.triggered_at

    ue_detail_count = uechecker.get_last_records_count()
    fp_detail_count = fpchecker.get_last_records_count()

    print('There are ', ue_detail_count, ' diners in ue_detail triggered_at', ue_triggered_at)
    print('There are ', fp_detail_count, ' diners in fp_detail triggered_at', fp_triggered_at)

    collection = 'stepfunction_log'

    db[collection].insert_one(
        {
            'ue_triggered_at': ue_triggered_at,
            'ue_detail_count': ue_detail_count,
            'fp_triggered_at': fp_triggered_at,
            'fp_detail_count': fp_detail_count,
            'matched': False
        }
        )
