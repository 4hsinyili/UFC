#  for db control
from pymongo import MongoClient

# for timing
import time
from datetime import datetime

# for email error
import logging
import logging.handlers

# home-made modules
# match and crawl
from Crawlers import match_uf, crawl_gm

# for file handling
import env
import conf


API_KEY = env.PLACE_API_KEY
MONGO_EC2_URI = env.MONGO_EC2_URI

DB_NAME = conf.DB_NAME
UE_DETAIL_COLLECTION = conf.UE_DETAIL_COLLECTION
FP_DETAIL_COLLECTION = conf.FP_DETAIL_COLLECTION
MATCHED_COLLECTION = conf.MATCHED_COLLECTION
STEPFUNCTION_LOG_COLLECTION = conf.STEPFUNCTION_LOG_COLLECTION

LOG_COLLECTION = conf.LOG_COLLECTION
GET_UE_DETAIL = conf.GET_UE_DETAIL
GET_FP_DETAIL = conf.GET_FP_DETAIL
MATCH = conf.MATCH
PLACE = conf.PLACE

admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client[DB_NAME]

print('Listen Starts at: ', datetime.utcnow())

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='log.log')

logger = logging.getLogger(__name__)

smtp_handler = logging.handlers.SMTPHandler(mailhost=('smtp.gmail.com', 587),
                                            fromaddr=env.ERROR_EMAIL,
                                            toaddrs=[env.MY_GMAIL],
                                            subject='Error',
                                            credentials=(env.ERROR_EMAIL,
                                                         env.ERROR_PWD),
                                            secure=())
logger.addHandler(smtp_handler)


def error(err_name, err):
    """Log Errors"""
    print("Something's wrong, check your mail.")
    logger.warning('error "%s" caused error "%s"', err_name, err)


def listen():
    pipeline = [{'$match': {'matched': False}}, {'$sort': {'_id': 1}}]
    cursor = db[STEPFUNCTION_LOG_COLLECTION].aggregate(pipeline=pipeline)
    results = list(cursor)
    cursor.close()
    if results == []:
        return False
    else:
        result = results[-1]
        _id = result['ue_triggered_at'].strftime('%Y-%m-%d')
        now = datetime.utcnow().strftime('%Y-%m-%d')
        if _id != now:
            return False
        else:
            return results[-1]


def main():
    record = listen()

    if not record:
        return False

    print('Start match.')

    time.sleep(mongo_write_buffer)

    triggered_at = record['ue_triggered_at']
    matcher = match_uf.Match(db,
                             read_collection_ue=UE_DETAIL_COLLECTION,
                             read_collection_fp=FP_DETAIL_COLLECTION,
                             write_collection=MATCHED_COLLECTION,
                             log_collection=LOG_COLLECTION,
                             w_triggered_by=MATCH,
                             triggered_by_ue=GET_UE_DETAIL,
                             triggered_by_fp=GET_FP_DETAIL,
                             triggered_at=triggered_at,
                             limit=limit)
    matcher.main()

    db['stepfunction_log'].update_one({'_id': record['_id']},
                                      {'$set': {
                                          'matched': True
                                      }})
    time.sleep(mongo_write_buffer)

    crawler = crawl_gm.GMCrawler(db,
                                 r_w_collection=MATCHED_COLLECTION,
                                 log_collection=LOG_COLLECTION,
                                 r_triggered_by=MATCH,
                                 w_triggered_by=PLACE,
                                 api_key=API_KEY,
                                 limit=limit)
    crawler.main()

    return True


if __name__ == '__main__':
    limit = 0
    execute_count = 0
    execute_limit = 12
    mongo_write_buffer = 10
    till_next_execute = 600
    while True:
        try:
            check_break = main()
            if check_break:
                break
            else:
                pass
            execute_count += 1
            if execute_count > execute_limit:
                print('Break now.')
                break
            print('Sleep now.')
            time.sleep(till_next_execute)
        except Exception as err:
            error('match uf error:', err)
            break
