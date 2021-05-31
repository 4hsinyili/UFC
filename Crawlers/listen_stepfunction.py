#  for db control
from pymongo import MongoClient
import time
from Crawlers import UF_combine

# for file handling
import env

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc_temp']


def listen():
    pipeline = [
        {
            '$match': {'matched': False}
        },
        {
            '$sort': {'_id': 1}
        }
    ]
    result = db['stepfunction_log'].aggregate(pipeline=pipeline)
    result = list(result)
    print(result)
    if result == []:
        return False
    else:
        return result[-1]


def main(comparison):
    result = listen()
    if result:
        result['matched'] = True
        comparison.main(db, collection, data_range)
        db['stepfunction_log'].update_one(
            {'_id': result['_id']},
            {'$set': {'matched': True}}
            )
        return True
    else:
        return False


if __name__ == '__main__':
    collection = 'matched'
    data_range = 0
    comparison = UF_combine.Comparison()
    check_break = main(comparison)
    while True:
        check_break = main(comparison)
        if check_break:
            break
        else:
            pass
        time.sleep(600)
