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

API_KEY = env.PLACE_API_KEY
MONGO_EC2_URI = env.MONGO_EC2_URI
admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client['ufc']
matched_checker = UF_match.MatchedChecker(db, 'matched', 'match')


class GMCrawler():
    def __init__(self, db, collection, matched_checker):
        self.db = db
        self.collection = collection
        self.matched_checker = matched_checker

    def update_from_previous_found(self):
        start = time.time()
        db = self.db
        collection = self.collection
        matched_checker = self.matched_checker
        triggered_at_gm = self.generate_triggered_at()
        last_week = triggered_at_gm - timedelta(weeks=1)
        triggered_at = matched_checker.get_triggered_at()
        print('Update from ', triggered_at_gm, 'to ', last_week, "'s found records")
        print('Will update ', triggered_at, "'s records.")
        pipeline = [
            {
                '$match': {
                    'triggered_at_gm': {
                                '$gte': last_week,
                                '$lt': triggered_at_gm,
                                "$exists": True
                                }
                        }
            }, {
                '$sort': {'triggered_at_gm': 1}
            }, {
                '$group': {
                    '_id': None,
                    'triggered_at_gm': {'$last': '$triggered_at_gm'},
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
        try:
            datas = next(cursor)['data']
            print('Record sample:')
            print(datas[0])
        except Exception:
            print('No old records to update.')
            cursor.close()
            return None
        for data in datas:
            loop_count += 1
            record = UpdateOne(
                {
                    'uuid_ue': data['uuid_ue'],
                    'uuid_fp': data['uuid_fp'],
                    'triggered_at': triggered_at
                }, {'$set': data}
            )
            update_records.append(record)
        cursor.close()
        print('There are ', loop_count, ' old records that could be used to update.')
        if len(update_records) > 0:
            result = db[collection].bulk_write(update_records)
        print('Bulk result:')
        print(result.bulk_api_result)
        stop = time.time()
        print('Update found took ', stop - start, ' s.')
        return result.modified_count

    def update_from_previous_not_found(self):
        start = time.time()
        db = self.db
        collection = self.collection
        matched_checker = self.matched_checker
        triggered_at_gm = self.generate_triggered_at()
        last_week = triggered_at_gm - timedelta(weeks=1)
        triggered_at = matched_checker.get_triggered_at()
        print('Update from ', triggered_at_gm, 'to ', last_week, "'s not found records")
        print('Will update ', triggered_at, "'s records.")
        pipeline = [
            {
                '$match': {
                    'not_found_gm': {
                                "$exists": True
                                },
                    'triggered_at': {
                                    '$gte': last_week,
                                    '$lt': triggered_at_gm,
                                    "$exists": True
                                    }
                        }
            },
            {
                '$group': {
                    '_id': None,
                    'data': {
                        "$addToSet": {
                            "uuid_ue": "$uuid_ue",
                            "uuid_fp": "$uuid_fp",
                            "uuid_gm": "$uuid_gm",
                            "title_gm": "$title_gm",
                            "rating_gm": "$rating_gm",
                            "view_count_gm": "$view_count_gm",
                            "link_gm": "$link_gm",
                            'not_found_gm': "$not_found_gm"
                        }
                    }
                }
            }
        ]
        cursor = db[collection].aggregate(pipeline)
        update_records = []
        loop_count = 0
        try:
            datas = next(cursor)['data']
            print('Record sample:')
            print(datas[0])
        except Exception:
            print('No old records to update.')
            cursor.close()
            return None
        for data in datas:
            loop_count += 1
            record = UpdateOne(
                {
                    'uuid_ue': data['uuid_ue'],
                    'uuid_fp': data['uuid_fp'],
                    'triggered_at': triggered_at
                }, {'$set': data}
            )
            update_records.append(record)
        cursor.close()
        print('There are ', loop_count, ' old records that could be used to update.')
        if len(update_records) > 0:
            result = db[collection].bulk_write(update_records)
        print('Bulk result:')
        print(result.bulk_api_result)
        stop = time.time()
        print('Update not found took ', stop - start, ' s.')
        return result.modified_count

    def get_targets(self, limit=0):
        db = self.db
        collection = self.collection
        matched_checker = self.matched_checker
        triggered_at = matched_checker.get_triggered_at()
        pipeline = [
            {
                '$match': {
                    'triggered_at': triggered_at,
                    "uuid_gm": {"$exists": False}
                    }
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
        cursor = db[collection].aggregate(pipeline=pipeline)
        return cursor

    def parse_troublesome_title(self, title):
        if title.startswith('麥當勞'):
            title = title.split(' ')[0]
        elif title.startswith('原果_Juice'):
            title = '原果_Juice'
        elif title.startswith('品川蘭'):
            title = title.split(' ')[0]
        elif title.startswith('拿坡里'):
            title = title.split(' ')[0]
        elif title.startswith('-55°C沙西米'):
            title = title.split(' (')[0]
        elif title.endswith('★)'):
            title = title.replace('★)', '')
        elif title.endswith('Ⓟ)'):
            title = title.replace('Ⓟ)', '')
        return title

    def parse_targets(self, cursor):
        parsed_targets = []
        for target in cursor:
            if target['title_ue'] == '':
                title = target['title_fp']
            else:
                title = target['title_ue']
            if target['gps_ue'] == []:
                gps = target['gps_fp']
            else:
                gps = target['gps_ue']
            title = self.parse_troublesome_title(title)
            parsed_target = {
                'title': title,
                'gps': f'{gps[0]},{gps[1]}',
                'triggered_at': target['triggered_at'],
                'uuid_ue': target['uuid_ue'],
                'uuid_fp': target['uuid_fp'],
            }
            parsed_targets.append(parsed_target)
        print('There are', len(parsed_targets), 'diners need to send to google map API')
        cursor.close()
        return parsed_targets

    def generate_triggered_at(self):
        now = datetime.utcnow()
        triggered_at = datetime.combine(now.date(), datetime.min.time())
        triggered_at = triggered_at.replace(hour=now.hour)
        return triggered_at

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

    def parse_places(self, places, target, triggered_at_gm):
        if (places['status'] == 'OK') and (places['candidates'] != []):
            try:
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
            except Exception:
                diner = {
                    'title_gm': '',
                    'rating_gm': 0,
                    'view_count_gm': 0,
                    'uuid_gm': '',
                    'link_gm': '',
                    'not_found_gm': True
                }
                return diner
        else:
            if 'error_message' in list(places.keys()):
                print(target['title'], 'has failed, due to', places['error_message'])
            else:
                print(target['title'], "has failed, due to can't find it on google map.")
            diner = {
                'title_gm': '',
                'rating_gm': 0,
                'view_count_gm': 0,
                'uuid_gm': '',
                'link_gm': '',
                'not_found_gm': True
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
                    }, {'$set': diner}
            )
            records.append(record)
        return records

    def save_to_matched(self, db, collection, records):
        db[collection].bulk_write(records)

    def save_triggered_at(self, triggered_at, records_count, update_found_count, update_not_found_count):
        db = self.db
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'records_count': records_count,
            'update_found_count': update_found_count,
            'update_not_found_count': update_not_found_count,
            'triggered_by': 'place'
            })

    def save_start_at(self):
        db = self.db
        triggered_at = self.matched_checker.get_triggered_at()
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'triggered_by': 'place_start',
            })

    def main(self, db, api_key, limit=0):
        self.save_start_at()
        db = self.db
        triggered_at_gm = self.generate_triggered_at()
        update_found_count = self.update_from_previous_found()
        update_not_found_count = self.update_from_previous_not_found()
        start = time.time()
        cursor = self.get_targets(limit)
        targets = self.parse_targets(cursor)
        diners = []
        for target in targets:
            url = self.get_url(target, api_key)
            places = self.find_places(url)
            diner = self.parse_places(places, target, triggered_at_gm)
            diner.update(target)
            for key in ['title', 'gps']:
                del diner[key]
            diners.append(diner)
        records = self.transfer_diners_to_records(diners)
        try:
            records_count = len(records)
            self.save_to_matched(db, 'matched', records)
            self.save_triggered_at(triggered_at_gm, records_count, update_found_count, update_not_found_count)
            print('Saved to db.')
        except Exception:
            pprint.pprint('No new diner need to send to GM.')
        stop = time.time()
        print('Send ', len(diners), ' to place API and save to db took: ', stop - start, 's.')


class GMChecker():
    def __init__(self, db, collection):
        self.db = db
        self. collection = collection
        self.triggered_at = self.get_triggered_at()

    def get_triggered_at(self):
        db = self.db
        collection = self.collection
        pipeline = [
            {
                '$sort': {'triggered_at': 1}
            },
            {
                '$group': {
                    '_id': None,
                    'triggered_at': {'$last': '$triggered_at'}
                    }
            }
        ]
        cursor = db[collection].aggregate(pipeline=pipeline)
        result = next(cursor)['triggered_at']
        cursor.close()
        return result

    def get_last_records(self, limit=0):
        db = self.db
        collection = self.collection
        triggered_at = self.triggered_at
        print(triggered_at)
        pipeline = [
            {'$match': {
                'triggered_at': triggered_at,
                'uuid_gm': {'$exists': True, '$ne': ''}
                }}
        ]
        if limit > 0:
            pipeline.append({'$limit': limit})
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result


if __name__ == '__main__':
    crawler = GMCrawler(db, 'matched', matched_checker)
    print('-----------before-------------')
    targets = crawler.get_targets(1)
    for target in targets:
        pprint.pprint(target)

    targets = crawler.get_targets(0)
    print(len(list(targets)))

    crawler.main(db, API_KEY, 0)

    print('-----------after-------------')
    targets = crawler.get_targets(1)
    for target in targets:
        pprint.pprint(target)

    targets = crawler.get_targets(0)
    print(len(list(targets)))

    print('----------should have gm------')
    checker = GMChecker(db, 'matched')
    cursor = checker.get_last_records(1)
    for target in cursor:
        del target['menu_ue']
        del target['menu_fp']
        pprint.pprint(target)
