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
    def get_targets(self, db, collection, matched_checker, limit=0):
        triggered_at = matched_checker.get_triggered_at()
        start = time.time()
        last_week = triggered_at - timedelta(weeks=1)
        grand_last_week = triggered_at - timedelta(weeks=2)
        pipeline = [
            {
                '$match': {
                    "$or": [
                        {'triggered_at': {
                            '$lt': last_week,
                            '$gte': grand_last_week
                            }},
                        {'triggered_at_gm': {'$exists': False}}
                    ]}
            }, {
                '$sort': {'triggered_at': -1}
            }, {
                '$group': {
                    '_id': '$uuid_ue',
                    'data': {
                        '$push': {
                            'title_ue': '$title_ue',
                            'title_fp': '$title_fp',
                            'gps_ue': '$gps_ue',
                            'gps_fp': '$gps_fp',
                            'triggered_at': '$triggered_at'}
                        }}
        stop = time.time()
        print('Update took ', stop - start, ' s.')
            }
        ]
        if limit > 0:
            pipeline.append({'$limit': limit})
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
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
