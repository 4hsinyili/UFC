#  for db control
from pymongo import MongoClient
import time
from datetime import datetime

try:
    from Crawlers import UF_match, GM_crawl
except Exception:
    print('Import Error at: ', datetime.utcnow())

# for file handling
import env

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD
API_KEY = env.PLACE_API_KEY
admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc']
print('Listen Starts at: ', datetime.utcnow())


def listen():
    pipeline = [
        {
            '$match': {'matched': False}
        },
        {
            '$sort': {'_id': 1}
        }
    ]
    cursor = db['stepfunction_log'].aggregate(pipeline=pipeline)
    result = list(cursor)
    cursor.close()
    if result == []:
        return False
    else:
        return result[-1]


def main(matcher, crawler):
    result = listen()
    if result:
        matcher.main(data_range)
        db['stepfunction_log'].update_one(
            {'_id': result['_id']},
            {'$set': {'matched': True}}
            )
        crawler.main(db, API_KEY, 0)
        return True
    else:
        return False


if __name__ == '__main__':
    collection = 'matched'
    data_range = 0
    macther = UF_match.Match(db, collection)
    matched_checker = UF_match.MatchedChecker(db, 'matched', 'match')
    crawler = GM_crawl.GMCrawler(db, 'matched', matched_checker)
    while True:
        check_break = main(macther, crawler)
        if check_break:
            break
        else:
            pass
        print('Sleep now')
        time.sleep(600)
