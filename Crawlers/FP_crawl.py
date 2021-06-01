# for db control
from pymongo import MongoClient, UpdateOne, InsertOne

# for crawling from API
import requests

# for file handling
import json
import env

# for timing and not to get caught
import time
import random
from datetime import datetime

# for preview
import pprint

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc']

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


class FPDinerDispatcher():
    def __init__(self, db, info_collection, offset=False, limit=False):
        self.db = db
        self.collection = info_collection
        self.triggered_at = self.get_triggered_at()
        self.diners_info = self.get_diners_info(info_collection, offset, limit)

    def get_triggered_at(self, collection='trigger_log'):
        db = self.db
        pipeline = [
            {
                '$match': {'triggered_by': 'get_fp_list'}
            },
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
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]['triggered_at']
        return result

    def get_diners_info(self, info_collection, offset=False, limit=False):
        db = self.db
        triggered_at = self.triggered_at
        pipeline = [
            {
                '$match': {
                    'title': {"$exists": True},
                    'triggered_at': triggered_at
                }
            }, {
                '$sort': {'uuid': 1}
                }
        ]
        if offset:
            pipeline.append({'$skip': offset})
        if limit:
            pipeline.append({'$limit': limit})
        result = db[info_collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def main(self):
        db = self.db
        temp_collection = 'fp_list_temp'
        diners_cursor = self.diners_info
        db[temp_collection].drop()
        records = []
        diners_count = 0
        for diner in diners_cursor:
            record = InsertOne(diner)
            records.append(record)
            diners_count += 1
        db[temp_collection].bulk_write(records)
        return diners_count


class FPDinerDetailCrawler():
    def __init__(self, target, db, info_collection, offset=False, limit=False):
        self.target = target
        self.db = db
        self.triggered_at = self.get_triggered_at()
        self.diners_info = self.get_diners_info(info_collection, offset, limit)

    def get_triggered_at(self, collection='trigger_log'):
        db = self.db
        pipeline = [
            {
                '$match': {'triggered_by': 'get_fp_list'}
            },
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
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]['triggered_at']
        return result

    def get_diners_info(self, info_collection, offset=False, limit=False):
        db = self.db
        triggered_at = self.triggered_at
        pipeline = [
            {
                '$match': {
                    'title': {"$exists": True},
                    'triggered_at': triggered_at
                    }
            }, {
                '$sort': {'uuid': 1}
            }
        ]
        if offset:
            pipeline.append({'$skip': offset})
        if limit:
            pipeline.append({'$limit': limit})
        result = db[info_collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def get_diner_detail_from_FP_API(self, diner):
        target = self.target
        error_log = {}
        try:
            diner_code = diner['uuid']
            now = datetime.utcnow()
            if now.hour+8 < 24:
                order_time = now.replace(hour=(now.hour+8)).strftime('%Y-%m-%dT%H:%M:%S')
            else:
                order_time = now.replace(day=(now.day+1), hour=(now.hour-16)).strftime('%Y-%m-%dT%H:%M:%S')
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
        now = datetime.utcnow()
        if now.hour+8 < 24:
            order_time = now.replace(hour=(now.hour+8)).strftime('%Y-%m-%dT%H:%M:%S')
        else:
            order_time = now.replace(day=(now.day+1), hour=(now.hour-16)).strftime('%Y-%m-%dT%H:%M:%S')
        error_log = {}
        try:
            fee_url = f'https://tw.fd-api.com/api/v5/vendors/{diner_code}/delivery-fee?&latitude={order_gps[0]}&longitude={order_gps[1]}&order_time={order_time}&basket_size=0&basket_currency=$&dynamic_pricing=0'
            fee_response = requests.get(fee_url, headers=headers)
            FP_API_response['deliver_fee'] = json.loads(fee_response.content)['fee']
        except Exception:
            error_log = {'error': 'fee_api wrong', 'diner': diner_code}
            return False, error_log
        return FP_API_response, error_log

    def get_diners_details(self, diners_cursor, data_range=0):
        if data_range == 0:
            diners_info = list(diners_cursor)
        else:
            diners_info = []
            for _ in range(data_range):
                diners_info.append(next(diners_cursor))
        diners = []
        error_logs = []
        loop_count = 0
        for diner in diners_info:
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
        print('There are ', len(diners_info), ' diners able to send to Appworks School.')
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
        diner['deliver_time'] = FP_API_response['minimum_delivery_time']
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
        open_hours = []
        open_days = set()
        for hours in business_hours:
            opening_type = hours['opening_type']
            if opening_type == 'delivering':
                weekday = hours['weekday']
                opening_time = hours['opening_time']
                closing_time = hours['closing_time']
                open_hour = (weekday, opening_time, closing_time)
                open_hours.append(open_hour)
                open_days.add(weekday)
        diner['open_hours'] = open_hours
        diner['open_days'] = list(open_days)
        return diner

    def save_triggered_at(self, triggered_at, records_count):
        db = self.db
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'records_count': records_count,
            'triggered_by': 'get_fp_detail'
            })

    def main(self, collection, data_range=0):
        db = self.db
        start = time.time()
        diners_cursor = self.diners_info
        diners, error_logs = self.get_diners_details(diners_cursor, data_range=data_range)
        triggered_at = self.triggered_at
        if error_logs == []:
            pass
        else:
            db[collection].insert_one({'uuid': '', 'triggered_at': triggered_at, 'error_logs': error_logs})
        if diners:
            records = []
            for diner in diners:
                if diner:
                    record = UpdateOne(
                        {'link': diner['link'], 'triggered_at': diner['triggered_at']},
                        {'$setOnInsert': diner},
                        upsert=True
                        )
                    records.append(record)
            db[collection].bulk_write(records)
        else:
            pprint.pprint('Error Logs:')
            pprint.pprint(error_logs)
        stop = time.time()
        if diners:
            print('Get ', len(diners), ' diner detail took ', stop - start, ' seconds.')
            self.save_triggered_at(triggered_at, len(diners))
        return diners, error_logs


class FPChecker():
    def __init__(self, db, collection, triggered_by):
        self.db = db
        self.collection = collection
        self.triggered_by = triggered_by
        self.triggered_at = self.get_triggered_at()

    def get_triggered_at(self, collection='trigger_log'):
        db = self.db
        pipeline = [
            {
                '$match': {'triggered_by': self.triggered_by}
            },
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
        result = db[collection].aggregate(pipeline=pipeline)
        result = list(result)[0]['triggered_at']
        return result

    def get_last_records(self, limit=0):
        db = self.db
        collection = self.collection
        triggered_at = self.triggered_at
        pipeline = [
            {
                '$match': {
                    'title': {"$exists": True},
                    'triggered_at': triggered_at
                }
            }, {
                '$sort': {'uuid': 1}
                }
        ]
        if limit > 0:
            pipeline.append({'$limit': limit})
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def get_last_records_count(self):
        db = self.db
        collection = self.collection
        triggered_at = self.triggered_at
        pipeline = [
            {
                '$match': {
                    'title': {"$exists": True},
                    'triggered_at': triggered_at
                    }
            }, {
                '$count': 'triggered_at'
                }
        ]
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return next(result)['triggered_at']

    def get_last_errorlogs(self):
        db = self.db
        collection = self.collection
        triggered_at = self.get_triggered_at()
        pipeline = [
            {
                '$match': {
                    'title': {"$exists": False},
                    'triggered_at': triggered_at
                }
            }
        ]
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def check_records(self, records, fields, data_range):
        loop_count = 0
        for record in records:
            if loop_count > data_range:
                break
            pprint.pprint([record[field] for field in fields])
            loop_count += 1


if __name__ == '__main__':
    running = {'list': False, 'detail': True, 'check': True}
    data_ranges = {'list': 0, 'detail': 10, 'check': 10}
    check_collection = 'fp_list'
    check_triggered_by = 'get_' + check_collection

    if running['list']:
        start = time.time()
        list_crawler = FPDinerListCrawler()
        diners_count_op = list_crawler.main(target, db=db, collection='fp_list')
        print('This time crawled ', diners_count_op, ' diners.')
        time.sleep(5)
        dispatcher = FPDinerDispatcher(db, 'fp_list')
        diners_count_ip = dispatcher.main()
        print('There are ', diners_count_ip, ' were latest triggered on fp_list.')
        print("Is dispatcher's input length >= list_crawler's output: ")
        print(diners_count_ip >= diners_count_op)

    if running['detail']:
        start = time.time()
        data_range = data_ranges['detail']
        detail_crawler = FPDinerDetailCrawler(target, db, 'fp_list', offset=False, limit=False)
        diners, error_logs = detail_crawler.main(collection='fp_detail', data_range=data_range)
        stop = time.time()
        time.sleep(5)
        pprint.pprint(stop - start)

    if running['check']:
        data_range = data_ranges['check']
        checker = FPChecker(db, check_collection, check_triggered_by)
        last_records = checker.get_last_records(data_range)
        errorlogs = checker.get_last_errorlogs()
        checker.check_records(last_records, ['title', 'deliver_time', 'triggered_at'], data_range)
        pprint.pprint(list(errorlogs))
