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

API_KEY = env.PLACE_API_KEY
MONGO_EC2_URI = env.MONGO_EC2_URI
admin_client = MongoClient(MONGO_EC2_URI)
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
        print('Start match.')
        time.sleep(120)
        matcher.main(data_range)
        db['stepfunction_log'].update_one(
            {'_id': result['_id']},
            {'$set': {'matched': True}}
            )
        time.sleep(10)
        crawler = GM_crawl.GMCrawler(db, 'matched', matched_checker)
        crawler.main(db, API_KEY, 0)
        return True
    else:
        return False


if __name__ == '__main__':
    collection = 'matched'
    data_range = 0
    loop_count = 0
    while True:
        macther = UF_match.Match(db, collection)
        matched_checker = UF_match.MatchedChecker(db, 'matched', 'match')
        check_break = main(macther)
        if check_break:
            break
        else:
            pass
        print('Sleep now')
        loop_count += 1
        if loop_count > 12:
            break
        time.sleep(600)
