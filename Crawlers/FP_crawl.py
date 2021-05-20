# for db control
from pymongo import MongoClient, UpdateOne

# for crawling from API
import requests

# for file handling
import os
from dotenv import load_dotenv
import json

# for timing and not to get caught
import time
import random
from datetime import datetime


load_dotenv()
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT"))
MONGO_ADMIN_USERNAME = os.getenv("MONGO_ADMIN_USERNAME")
MONGO_ADMIN_PASSWORD = os.getenv("MONGO_ADMIN_PASSWORD")

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc_temp']

target = {
    'name': 'Appworks School',
    'address': '110台北市信義區基隆路一段178號',
    'gps': (25.0424488, 121.562731)
}
driver_path = os.getenv('DEIVER_PATH')


class FPDinerListCrawler():
    def get_diners_info_from_FP_API(self, target):
        now = datetime.now()
        triggered_at = datetime.combine(now.date(), datetime.min.time())
        triggered_at = triggered_at.replace(hour=now.hour)
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
            return False, error_log
        try:
            r = requests.get(url, headers=headers)
        except Exception:
            error_log = {'error': 'vendors_api wrong', 'triggered_at': triggered_at}
            print('vendors_api wrong')
            return False, error_log
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
            return False, error_log
        return diners_info, error_log

    def main(self, target, db, collection):
        # self.chrome_close(self.driver)
        diners_info, error_log = self.get_diners_info_from_FP_API(target)
        # print(len(diners_info))
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
        else:
            # print(diners_info)
            print(error_log['error'])


class FPDinerDetailCrawler():
    def __init__(self, diners_info_collection):
        self.diners_info = self.get_diners_info(diners_info_collection)

    def get_diners_info(self, diners_info_collection):
        pipeline = [
            {'$sort': {'triggered_at': -1}},
            {'$group': {
                '_id': {
                    'title': '$title',
                    'link': '$link',
                    'deliver_fee': '$deliver_fee',
                    'deliver_time': '$deliver_time',
                    'FP_choice': '$FP_choice',
                    'uuid': '$uuid',
                    'triggered_at': '$triggered_at'
                },
                'triggered_at': {'$last': '$triggered_at'}
            }}
        ]
        result = db[diners_info_collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def get_diner_detail_from_FP_API(self, diner):
        error_log = {}
        try:
            diner_code = diner['uuid']
            order_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            order_gps = target['gps']
        except Exception:
            error_log = {'error': 'diner_info wrong', 'diner': diner}
            return False, error_log
        try:
            headers = {
                'User-Agent':
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
                'x-disco-client-id': 'web'
            }
            vendor_url = f"""https://tw.fd-api.com/api/v5/vendors/{diner_code}?include=menus&language_id=6&dynamic_pricing=0&opening_type=delivery&order_time={order_time}%2B0800&latitude={order_gps[0]}&longitude={order_gps[1]}"""
            vendor_response = requests.get(vendor_url, headers=headers)
            FP_API_response = json.loads(vendor_response.content)['data']
        except Exception:
            error_log = {'error': 'vendor_api wrong', 'diner': diner['uuid']}
            return False, error_log
        try:
            if FP_API_response['is_active']:
                FP_API_response, error_log = self.get_diner_fee(FP_API_response, diner_code, order_gps, headers)
        except Exception:
            FP_API_response['deliver_fee'] = 0
        if FP_API_response:
            diner, error_log = self.clean_FP_API_response(FP_API_response, diner)
            time.sleep(0.5)
            return diner, error_log
        else:
            return False, error_log

    def get_diner_fee(self, FP_API_response, diner_code, order_gps, headers):
        time.sleep(0.5)
        error_log = {}
        try:
            fee_url = f'https://tw.fd-api.com/api/v5/vendors/{diner_code}/delivery-fee?&latitude={order_gps[0]}&longitude={order_gps[1]}&order_time=now&basket_size=0&basket_currency=$&dynamic_pricing=0'
            fee_response = requests.get(fee_url, headers=headers)
            FP_API_response['deliver_fee'] = json.loads(fee_response.content)['fee']
        except Exception:
            error_log = {'error': 'fee_api wrong', 'diner': diner_code}
            return False, error_log
        return FP_API_response, error_log

    def get_diners_details(self, data_range=0):
        if data_range == 0:
            diners_info = self.diners_info
        else:
            diners_info = self.diners_info[:data_range]
        diners = []
        error_logs = []
        loop_count = 0
        for diner in diners_info:
            diner = diner['_id']
            diner, error_log = self.get_diner_detail_from_FP_API(diner)
            if diner:
                diners.append(diner)
            if error_log == {}:
                pass
            else:
                error_logs.append(error_log)
            loop_count += 1
            if loop_count % 500 == 0:
                time.sleep(random.randint(10, 30))
        return diners, error_logs

    def clean_FP_API_response(self, FP_API_response, diner):
        error_log = {}
        try:
            diner = self.get_diner_menu(FP_API_response, diner)
        except Exception:
            error_log = {'error': 'get menu wrong', 'diner': diner['uuid']}
            return False, error_log
        try:
            diner = self.get_open_hours(FP_API_response, diner)
        except Exception:
            error_log = {'error': 'get open hours wrong', 'diner': diner['uuid']}
            return False, error_log
        try:
            diner = self.get_other_info(FP_API_response, diner)
        except Exception:
            error_log = {'error': 'get other info wrong', 'diner': diner['uuid']}
            return False, error_log
        return diner, error_log

    def get_other_info(self, FP_API_response, diner):
        diner['deliver_time'] = str(FP_API_response['minimum_delivery_time']) + ' 分鐘'
        diner['deliver_fee'] = FP_API_response['deliver_fee']
        diner['budget'] = FP_API_response['budget']
        diner['rating'] = FP_API_response['rating']
        diner['view_count'] = FP_API_response['review_number']
        diner['image'] = FP_API_response['hero_image']
        food_characteristics = [
            i['name'] for i in FP_API_response['food_characteristics']
        ]
        cuisines = [i['name'] for i in FP_API_response['cuisines']]
        diner['tags'] = food_characteristics + cuisines
        diner['address'] = FP_API_response['address']
        diner['gps'] = (FP_API_response['latitude'],
                        FP_API_response['longitude'])
        return diner

    def get_diner_menu(self, FP_API_response, diner):
        menu = []
        sections = FP_API_response['menus']
        for section in sections:
            section_uuid = section['id']
            section_title = section['name']
            subsections = section['menu_categories']
            for subsection in subsections:
                subsection_id = subsection['id']
                subsection_title = subsection['name']
                items = subsection['products']
                items_list = []
                for item in items:
                    item_uuid = item['id']
                    item_description = item['description']
                    item_price = item['product_variations'][0]['price']
                    item_title = item['name']
                    raw_image = item['images']
                    if len(raw_image) > 0:
                        item_image_url = raw_image[0]['image_url']
                    else:
                        item_image_url = ''
                    items_list.append({
                        'item_uuid': item_uuid,
                        'item_title': item_title,
                        'item_price': item_price,
                        'item_image_url': item_image_url,
                        'item_description': item_description,
                    })
                menu.append({
                    'section_id': section_uuid,
                    'section_title': section_title,
                    'subsection_id': subsection_id,
                    'subsection_title': subsection_title,
                    'items': items_list
                })
        diner['menu'] = menu
        return diner

    def get_open_hours(self, FP_API_response, diner):
        business_hours = FP_API_response['schedules']
        day_map = {
            1: 'Mon.',
            2: 'Tue.',
            3: 'Wed.',
            4: 'Thu.',
            5: 'Fri.',
            6: 'Sat.',
            7: 'Sun.',
        }
        open_hours = []
        for hours in business_hours:
            opening_type = hours['opening_type']
            if opening_type == 'delivering':
                weekday = hours['weekday']
                weekday = day_map[weekday]
                opening_time = hours['opening_time']
                closing_time = hours['closing_time']
                open_hour = (weekday, opening_time, closing_time)
                open_hours.append(open_hour)
        diner['open_hours'] = open_hours
        return diner

    def main(self, db, collection, data_range):
        diners, error_logs = self.get_diners_details(data_range=data_range)
        triggered_at = diners[0]['triggered_at']
        if error_logs == []:
            pass
        else:
            db[collection].insert_one({'uuid': '', 'triggered_at': triggered_at, 'error_logs': error_logs})
        if diners:
            records = [UpdateOne(
                {'uuid': record['uuid'], 'triggered_at': record['triggered_at']},
                {'$setOnInsert': record},
                upsert=True
            ) for record in diners]
            db[collection].bulk_write(records)
        else:
            # print(diners_info)
            print(error_logs)
        return diners, error_logs


class FPChecker():
    def __init__(self, db, collection, pipeline):
        self.db = db
        self.collection = collection
        self.pipeline = pipeline

    def get_last_records(self):
        db = self.db
        collection = self.collection
        pipeline = self.pipeline
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result


if __name__ == '__main__':
    # start = time.time()
    # d_list_crawler = FPDinerListCrawler()
    # d_list_crawler.main(target, db=db, collection='fp_list')
    # stop = time.time()
    # print(stop - start)

    # time.sleep(10)

    d_detail_crawler = FPDinerDetailCrawler('fp_list')
    start = time.time()
    diners, error_logs = d_detail_crawler.main(db=db, collection='fp_detail', data_range=0)
    stop = time.time()
    print(stop - start)

    pipeline = [
            {'$sort': {'triggered_at': -1}},
            {'$group': {
                '_id': {
                    'title': '$title',
                    'link': '$link',
                    'deliver_fee': '$deliver_fee',
                    'deliver_time': '$deliver_time',
                    'FP_choice': '$FP_choice',
                    'uuid': '$uuid',
                    'triggered_at': '$triggered_at',
                    'menu': '$menu',
                    'budget': '$budget',
                    'rating': '$rating',
                    'view_count': '$view_count',
                    'image': '$image',
                    'tags': '$tags',
                    'address': '$address',
                    'gps': '$gps',
                    'open_hours': '$open_hours',
                },
                'triggered_at': {'$last': '$triggered_at'}
            }}
        ]
    checker = FPChecker(db, 'fp_detail', pipeline)
    last_records = checker.get_last_records()
