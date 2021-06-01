# for db control
from pymongo import UpdateOne

# for crawling from API
import requests

# for file handling
import json

# for timing and not to get caught
from datetime import datetime
import time

# for preview
import pprint

target = {
    'title': 'Appworks School',
    'address': '110台北市信義區基隆路一段178號',
    'gps': (25.0424488, 121.562731)
}


class FPDinerListCrawler():
    def get_diners_info_from_FP_API(self, target):
        now = datetime.utcnow()
        triggered_at = datetime.combine(now.date(), datetime.min.time())
        triggered_at = triggered_at.replace(hour=now.hour)
        print('Start getting diners list of ', target['title'], 'begin at', triggered_at, '.')
        error_log = {}
        headers = {
            'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            'x-disco-client-id': 'web'
        }
        limit = 20000
        offset = 0
        try:
            url = f"""https://disco.deliveryhero.io/listing/api/v1/pandora/vendors?latitude={target['gps'][0]}&longitude={target['gps'][1]}&language_id=6&include=characteristics&dynamic_pricing=0&configuration=Original&country=tw&customer_id=&\
                customer_hash=&budgets=&cuisine=&sort=&food_characteristic=&use_free_delivery_label=false&vertical=restaurants&limit={limit}&offset={offset}&customer_type=regular"""
        except Exception:
            error_log = {'error': 'target value wrong', 'triggered_at': triggered_at}
            print('target value wrong')
            return False, error_log, triggered_at
        try:
            r = requests.get(url, headers=headers)
        except Exception:
            error_log = {'error': 'vendors_api wrong', 'triggered_at': triggered_at}
            print('vendors_api wrong')
            return False, error_log, triggered_at
        try:
            FP_API_response = json.loads(r.content)
            diners = FP_API_response['data']['items']
            diners_info = []
            for diner in diners:
                link = diner['redirection_url']
                title = diner['name']
                uuid = diner['code']
                FP_choice = int(diner['is_best_in_city'])
                deliver_fee = diner['minimum_delivery_fee']
                deliver_time = diner['minimum_delivery_time']
                result = {
                    'title': title,
                    'link': link,
                    'deliver_fee': deliver_fee,
                    'deliver_time': deliver_time,
                    'FP_choice': FP_choice,
                    'uuid': uuid,
                    'triggered_at': triggered_at
                }
                diners_info.append(result)
        except Exception:
            error_log = {'error': 'parse vendors_api response wrong', 'triggered_at': triggered_at}
            print('parse vendors_api response wrong')
            return False, error_log, triggered_at
        return diners_info, error_log, triggered_at

    def save_triggered_at(self, target, db, triggered_at, records_count):
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'records_count': records_count,
            'triggered_by': 'get_fp_list',
            'target': target
            })

    def main(self, target, db, collection):
        start = time.time()
        diners_info, error_log, triggered_at = self.get_diners_info_from_FP_API(target)
        print('There are ', len(diners_info), ' diners successfully paresed.')
        if error_log == {}:
            pass
        else:
            db[collection].insert_one(error_log)
        if diners_info:
            records = [UpdateOne(
                {'uuid': record['uuid'], 'triggered_at': record['triggered_at']},
                {'$setOnInsert': record},
                upsert=True
            ) for record in diners_info]
            db[collection].bulk_write(records)
            self.save_triggered_at(target, db, triggered_at, len(diners_info))
        else:
            pprint.pprint('Error Logs:')
            pprint.pprint(error_log)
        stop = time.time()
        print('Get diner list near ', target['title'], ' took ', stop - start, ' seconds.')
        return len(diners_info)
