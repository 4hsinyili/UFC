# for db control
from pymongo import MongoClient, UpdateOne

# for file handling
import env

# for timing and not to get caught
# import time
# import random
from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta

# for preview
import pprint
import time

import requests
from urllib.parse import urlencode

# home-made module
from Crawlers import UF_match

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
matched_checker = UF_match.MatchedChecker(db, 'matched', 'match')


class GMCrawler():
    def __init__(self, db, collection, matched_checker):
        self.db = db
        self.collection = collection
        self.matched_checker = matched_checker

    def update_from_previous(self):
        start = time.time()
        db = self.db
        collection = self.collection
        matched_checker = self.matched_checker
        triggered_at = self.generate_triggered_at()
        print(triggered_at)
        last_week = triggered_at - timedelta(weeks=1)
        print(last_week)
        pipeline = [
            {
                '$match': {
                    'triggered_at': {
                                '$gte': last_week,
                                '$lt': triggered_at
                                },
                    'uuid_gm': {"$exists": True}}
            }, {
                '$sort': {'triggered_at': 1}
            }, {
                '$group': {
                    '_id': None,
                    'triggered_at': {'$last': '$triggered_at'},
                    'data': {
                        "$addToSet": {
                            "uuid_ue": "$uuid_ue",
                            "uuid_fp": "$uuid_fp",
                            "uuid_gm": "$uuid_gm",
                            "title_gm": "$title_gm",
                            "rating_gm": "$rating_gm",
                            "view_count_gm": "$view_count_gm",
                            "link_gm": "$link_gm",
                        }
                    }
                }
            }
        ]
        cursor = db[collection].aggregate(pipeline)
        update_records = []
        loop_count = 0
        last_triggered_at = matched_checker.triggered_at
        try:
            datas = next(cursor)['data']
            for data in datas:
                loop_count += 1
                record = UpdateOne(
                    {
                        'uuid_ue': data['uuid_ue'],
                        'uuid_fp': data['uuid_fp'],
                        'triggered_at': last_triggered_at
                        }, {'$set': data}, upsert=True
                )
                update_records.append(record)
        except Exception:
            pass
        print('There are ', loop_count, ' diners updated using old records.')
        if len(update_records) > 0:
            db[collection].bulk_write(update_records)
        stop = time.time()
        print('Update took ', stop - start, ' s.')

    def get_targets(self, limit=0):
        db = self.db
        collection = self.collection
        matched_checker = self.matched_checker
        triggered_at = matched_checker.triggered_at
        pipeline = [
            {
                '$match': {
                    'triggered_at_gm': {'$exists': False},
                    'triggered_at': triggered_at}
            }, {
                '$sort': {'_id': 1}
            }, {
                '$project': {
                    '_id': 0,
                    'uuid_ue': 1,
                    'title_ue': 1,
                    'gps_ue': 1,
                    'uuid_fp': 1,
                    'title_fp': 1,
                    'gps_fp': 1,
                    'triggered_at': 1,
                    }
            }
        ]
        if limit > 0:
            pipeline.append({'$limit': limit})
        result = db[collection].aggregate(pipeline=pipeline)
        return result

    def generate_triggered_at():
        now = datetime.now()
        triggered_at = datetime.combine(now.date(), datetime.min.time())
        triggered_at = triggered_at.replace(hour=now.hour)
        return triggered_at

    def parse_targets(self, targets):
        parsed_targets = []
        for target in targets:
            target = target['data']
            if target['title_fp'] == '':
                title = target['title_ue']
            else:
                title = target['title_fp']
            if target['gps_fp'] == '':
                gps = target['gps_ue']
            else:
                gps = target['gps_fp']
            parsed_target = {
                'title': title,
                'gps': tuple(gps),
                'triggered_at': target['triggered_at'],
                'uuid_ue': target['uuid_ue'],
                'uuid_fp': target['uuid_fp'],
            }
            parsed_targets.append(parsed_target)
        return parsed_targets

    def get_url(self, target, api_key):
        data_type = 'json'
        endpoint = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/{data_type}"
        params = {
            "input": target['title'],
            "inputtype": "textquery",
            "key": api_key,
            'locationbias': f"circle:50@{target['gps']}",
            "language": "zh-TW",
            "fields": "name,rating,user_ratings_total,place_id"
        }
        url_params = urlencode(params)
        url = f"{endpoint}?{url_params}"
        return url

    def find_places(self, url):
        r = requests.get(url)
        places = r.json()
        return places

    def parse_places(self, places, triggered_at_gm):
        if (places['status'] == 'OK') and (places['candidates'] != []):
            place = places['candidates'][0]
            diner = {
                'title_gm': place['name'],
                'rating_gm': place['rating'],
                'view_count_gm': place['user_ratings_total'],
                'uuid_gm': place['place_id'],
                'link_gm': 'https://www.google.com/maps/place/?q=place_id:' + place['place_id'],
                'triggered_at_gm': triggered_at_gm

            }
            return diner
        else:
            diner = {
                'title_gm': '',
                'rating_gm': 0,
                'view_count_gm': 0,
                'uuid_gm': '',
                'link_gm': '',
                'triggered_at_gm': triggered_at_gm
            }
            return diner

    def transfer_diners_to_records(self, diners):
        records = []
        for diner in diners:
            record = UpdateOne(
                {
                    'uuid_ue': diner['uuid_ue'],
                    'uuid_fp': diner['uuid_fp'],
                    'triggered_at': diner['triggered_at']
                    }, {'$setOnInsert': diner}, upsert=True
            )
            records.append(record)
        return records

    def save_to_gm_placed(self, db, collection, records):
        db[collection].bulk_write(records)

    def save_to_matched(self, db, collection, records):
        db[collection].bulk_write(records)

    def main(self, db, matched_checker, api_key, limit=0):
        triggered_at_gm = self.generate_triggered_at()
        targets = self.get_targets(db, 'matched', matched_checker, limit)
        start = time.time()
        targets = self.parse_targets(targets)
        diners = []
        for target in targets:
            url = self.get_url(target, api_key)
            places = self.find_places(url)
            diner = self.parse_places(places, triggered_at_gm)
            diner.update(target)
            for key in ['title', 'gps']:
                del diner[key]
                diners.append(diner)
            else:
                continue
        records = self.transfer_diners_to_records(diners)
        self.save_to_matched(db, 'matched', records)
        self.save_to_gm_placed(db, 'gm_placed', records)
        pprint.pprint(diners[0])
        stop = time.time()
        print('Send ', len(diners), ' to place API and save to db took: ', stop - start, 's.')


if __name__ == '__main__':
    crawler = GMCrawler()
    # crawler.main(db, matched_checker, API_KEY, 10)
    targets = crawler.get_targets(db, 'matched', matched_checker, 1)
    pprint.pprint(next(targets))
