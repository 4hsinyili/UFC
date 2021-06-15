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

MONGO_EC2_URI = env.MONGO_EC2_URI
admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client['ufc']

target = {
    'title': 'Appworks School',
    'address': '110台北市信義區基隆路一段178號',
    'gps': (25.0424488, 121.562731)
}


class FPDinerListCrawler():
    def __init__(self, target, fp_list_url, headers, db, write_collection, offset, limit):
        self.target = target
        self.headers = headers
        self.db = db
        self.write_collection = write_collection
        self.fp_list_url = fp_list_url
        self.offset = offset
        self.limit = limit
        self.end_point = self.generate_fp_list_endpoint()
        self.triggered_at = self.generate_triggered_at()

    def generate_triggered_at(self):
        now = datetime.utcnow()
        triggered_at = datetime.combine(now.date(), datetime.min.time())
        triggered_at = triggered_at.replace(hour=now.hour)
        return triggered_at

    def generate_fp_list_endpoint(self):
        fp_list_url = self.fp_list_url
        latitude = str(self.target['gps'][0])
        longitude = str(self.target['gps'][1])
        limit = str(self.limit)
        offset = str(self.offset)
        end_point = fp_list_url.replace('{latitude}', latitude)
        end_point = end_point.replace('{longitude}', longitude)
        end_point = end_point.replace('{limit}', limit)
        end_point = end_point.replace('{offset}', offset)
        return end_point

    def parse_diners(self, diners, triggered_at):
        data = []
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
            data.append(result)
        return data

    def get_diners_info_from_FP_API(self, target):
        triggered_at = self.triggered_at
        print('Start getting diners list of ', target['title'], 'begin at', triggered_at, '.')
        error_log = {}

        try:
            end_point = self.end_point
        except Exception:
            error_log = {'error': 'target value wrong', 'triggered_at': triggered_at}
            print('target value wrong')
            return False, error_log, triggered_at

        try:
            list_response = requests.get(end_point, headers=self.headers)
        except Exception:
            error_log = {'error': 'vendors_api wrong', 'triggered_at': triggered_at}
            print('vendors_api wrong')
            return False, error_log, triggered_at

        try:
            list_ = json.loads(list_response.content)
            diners = list_['data']['items']
            diners_info = self.parse_diners(diners, triggered_at)
        except Exception:
            error_log = {'error': 'parse vendors_api response wrong', 'triggered_at': triggered_at}
            print('parse vendors_api response wrong')
            return False, error_log, triggered_at

        return diners_info, error_log, triggered_at

    def save_triggered_at(self, target, db, triggered_at, records_count, batch_id):
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'records_count': records_count,
            'triggered_by': 'get_fp_list',
            'batch_id': batch_id,
            'target': target
            })

    def save_start_at(self, target, db):
        now = datetime.utcnow()
        batch_id = now.timestamp()
        triggered_at = self.triggered_at
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'triggered_by': 'get_fp_list_start',
            'batch_id': batch_id,
            'target': target
            })
        return batch_id

    def main(self):
        start = time.time()
        db = self.db
        write_collection = self.write_collection
        target = self.target
        batch_id = self.save_start_at(target, db)

        diners_info, error_log, triggered_at = self.get_diners_info_from_FP_API(target)
        print('There are ', len(diners_info), ' diners successfully paresed.')

        if error_log == {}:
            pass
        else:
            db[write_collection].insert_one(error_log)

        if diners_info:
            records = [UpdateOne(
                {'uuid': record['uuid'], 'triggered_at': record['triggered_at']},
                {'$setOnInsert': record},
                upsert=True
            ) for record in diners_info]
            db[write_collection].bulk_write(records)
            self.save_triggered_at(target, db, triggered_at, len(diners_info), batch_id)
        else:
            pprint.pprint('Error Logs:')
            pprint.pprint(error_log)

        stop = time.time()
        print('Get diner list near ', target['title'], ' took ', stop - start, ' seconds.')

        return len(diners_info)


class FPDinerDispatcher():
    def __init__(self, db, read_collection, write_collection='fp_list_temp', offset=False, limit=False):
        self.db = db
        self.read_collection = read_collection
        self.write_collection = write_collection
        self.triggered_at = self.get_triggered_at()
        self.diners_cursor = self.get_diners_info(offset, limit)

    def get_triggered_at(self, tirggered_by='get_fp_list', collection='trigger_log'):
        db = self.db
        pipeline = [
            {
                '$match': {'triggered_by': tirggered_by}
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
        cursor = db[collection].aggregate(pipeline=pipeline)
        result = next(cursor)['triggered_at']
        cursor.close()
        return result

    def get_diners_info(self, offset=False, limit=False):
        db = self.db
        triggered_at = self.triggered_at
        read_collection = self.read_collection
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
        result = db[read_collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def main(self):
        db = self.db
        write_collection = self.write_collection
        diners_cursor = self.diners_cursor
        db[write_collection].drop()
        records = []
        diners_count = 0
        for diner in diners_cursor:
            record = InsertOne(diner)
            records.append(record)
            diners_count += 1
        db[write_collection].bulk_write(records)
        return diners_count


class FPDinerDetailCrawler():
    def __init__(self, target, fp_detail_url, fp_deliver_fee_url, headers, db, read_collection, write_collection, log_collection, triggered_by, offset=False, limit=False):
        self.target = target
        self.headers = headers
        self.db = db
        self.read_collection = read_collection
        self.write_collection = write_collection
        self.log_collection = log_collection
        self.triggered_by = triggered_by
        self.triggered_at, self.batch_id = self.get_pre_run_info()
        self.diners_cursor = self.get_diners_cursor(read_collection, offset, limit)
        self.fp_detail_url = fp_detail_url
        self.fp_deliver_fee_url = fp_deliver_fee_url
        self.order_time = self.generate_order_time()
        self.limit = limit

    def get_pre_run_info(self):
        db = self.db
        tirggered_by = self.triggered_by
        log_collection = self.log_collection
        pipeline = [
            {
                '$match': {'triggered_by': tirggered_by}
            },
            {
                '$sort': {'triggered_at': 1}
            },
            {
                '$group': {
                    '_id': None,
                    'triggered_at': {'$last': '$triggered_at'},
                    'batch_id': {'$last': '$batch_id'}
                    }
            }
        ]
        cursor = db[log_collection].aggregate(pipeline=pipeline)
        raw = next(cursor)
        triggered_at = raw['triggered_at']
        batch_id = raw['batch_id']
        cursor.close()
        return triggered_at, batch_id

    def get_diners_cursor(self, read_collection, offset=False, limit=False):
        db = self.db
        triggered_at = self.triggered_at
        read_collection = self.read_collection
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
        cursor = db[read_collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return cursor

    def generate_order_time(self):
        now = datetime.utcnow()
        if now.hour + 8 < 24:
            order_time = now.replace(hour=(now.hour+8)).strftime('%Y-%m-%dT%H:%M:%S')
        else:
            order_time = now.replace(day=(now.day+1), hour=(now.hour-16)).strftime('%Y-%m-%dT%H:%M:%S')
        return order_time

    def generate_detail_end_point(self, uuid):
        fp_detail_url = self.fp_detail_url
        order_time = self.order_time
        latitude = str(self.target['gps'][0])
        longitude = str(self.target['gps'][1])
        end_point = fp_detail_url.replace('{uuid}', uuid)
        end_point = end_point.replace('{order_time}', order_time)
        end_point = end_point.replace('{latitude}', latitude)
        end_point = end_point.replace('{longitude}', longitude)
        return end_point

    def get_diner_detail_from_api(self, diner):
        headers = self.headers
        error_log = {}

        try:
            uuid = diner['uuid']
        except Exception:
            error_log = {'error': 'parse_diner_info wrong', 'diner': diner}
            return False, error_log

        try:
            detail_end_point = self.generate_detail_end_point(uuid)
            detail_response = requests.get(detail_end_point, headers=headers)
            detail = json.loads(detail_response.content)['data']
        except Exception:
            error_log = {'error': 'vendor_api wrong', 'diner': diner['uuid']}
            return False, error_log

        if detail['is_active']:
            detail = self.get_diner_fee_from_api(detail, uuid)

        if detail:
            diner, error_log = self.clean_detail_response(detail, diner)
            time.sleep(0.5)
            return diner, error_log
        else:
            return False, error_log

    def generate_fee_end_point(self, uuid):
        fp_deliver_fee_url = self.fp_deliver_fee_url
        order_time = self.order_time
        latitude = str(self.target['gps'][0])
        longitude = str(self.target['gps'][1])
        end_point = fp_deliver_fee_url.replace('{uuid}', uuid)
        end_point = end_point.replace('{order_time}', order_time)
        end_point = end_point.replace('{latitude}', latitude)
        end_point = end_point.replace('{longitude}', longitude)
        return end_point

    def get_diner_fee_from_api(self, detail, uuid):
        time.sleep(0.5)
        headers = self.headers
        try:
            fee_endpoint = self.generate_fee_end_point(uuid)
            fee_response = requests.get(fee_endpoint, headers=headers)
            detail['deliver_fee'] = json.loads(fee_response.content)['fee']
        except Exception:
            detail['deliver_fee'] = 0
        return detail

    def get_diners_details(self, data_range=0):
        diners_cursor = self.diners_cursor
        diners_info = list(diners_cursor)
        diners = []
        error_logs = []
        loop_count = 0
        for diner in diners_info:
            diner, error_log = self.get_diner_detail_from_api(diner)
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

    def clean_detail_response(self, detail, diner):
        error_log = {}
        try:
            diner = self.get_diner_menu(detail, diner)
        except Exception:
            error_log = {'error': 'get menu wrong', 'diner': diner['uuid']}
            return False, error_log
        try:
            diner = self.get_open_hours(detail, diner)
        except Exception:
            error_log = {'error': 'get open hours wrong', 'diner': diner['uuid']}
            return False, error_log
        try:
            diner = self.get_other_info(detail, diner)
        except Exception:
            error_log = {'error': 'get other info wrong', 'diner': diner['uuid']}
            return False, error_log
        return diner, error_log

    def get_other_info(self, detail, diner):
        diner['deliver_time'] = detail['minimum_delivery_time']
        diner['deliver_fee'] = detail['deliver_fee']
        diner['budget'] = detail['budget']
        diner['rating'] = detail['rating']
        diner['view_count'] = detail['review_number']
        diner['image'] = detail['hero_image']
        food_characteristics = [
            i['name'] for i in detail['food_characteristics']
        ]
        cuisines = [i['name'] for i in detail['cuisines']]
        diner['tags'] = food_characteristics + cuisines
        diner['address'] = detail['address']
        diner['gps'] = (detail['latitude'],
                        detail['longitude'])
        return diner

    def get_diner_menu(self, detail, diner):
        menu = []
        item_dict = {}
        sections = detail['menus']
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
                    item_dict[item_title] = item_price
                menu.append({
                    'section_id': section_uuid,
                    'section_title': section_title,
                    'subsection_id': subsection_id,
                    'subsection_title': subsection_title,
                    'items': items_list
                })
        diner['menu'] = menu
        diner['item_pair'] = item_dict
        return diner

    def get_open_hours(self, detail, diner):
        business_hours = detail['schedules']
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

    def save_triggered_at(self, records_count):
        db = self.db
        trigger_log = self.log_collection
        db[trigger_log].insert_one({
            'triggered_at': self.triggered_at,
            'records_count': records_count,
            'triggered_by': self.triggered_by,
            'batch_id': self.batch_id
            })

    def save_records(self, diners):
        write_collection = self.write_collection
        records = []
        for diner in diners:
            if diner:
                record = UpdateOne(
                    {'link': diner['link'], 'triggered_at': diner['triggered_at']},
                    {'$setOnInsert': diner},
                    upsert=True
                    )
                records.append(record)
        db[write_collection].bulk_write(records)
        return len(records)

    def main(self):
        db = self.db
        write_collection = self.write_collection
        triggered_at = self.triggered_at
        limit = self.limit

        start = time.time()
        diners, error_logs = self.get_diners_details(limit)
        if error_logs == []:
            pass
        else:
            db[write_collection].insert_one({'uuid': '', 'triggered_at': triggered_at, 'error_logs': error_logs})
        if diners:
            diners_count = self.save_records(diners)
        else:
            pprint.pprint('Error Logs:')
            pprint.pprint(error_logs)
        stop = time.time()
        if diners:
            print('Get ', diners_count, ' diner detail took ', stop - start, ' seconds.')
            self.save_triggered_at(diners_count)
        return diners, error_logs


class FPChecker():
    def __init__(self, db, read_collection, triggered_by):
        self.db = db
        self.read_collection = read_collection
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
        cursor = db[collection].aggregate(pipeline=pipeline)
        result = next(cursor)['triggered_at']
        cursor.close()
        return result

    def get_latest_records(self, limit=0):
        db = self.db
        read_collection = self.read_collection
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
        result = db[read_collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result

    def get_latest_records_count(self):
        db = self.db
        read_collection = self.read_collection
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
        cursor = db[read_collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        result = next(cursor)['triggered_at']
        return result

    def get_latest_errorlogs(self):
        db = self.db
        read_collection = self.read_collection
        triggered_at = self.get_triggered_at()
        pipeline = [
            {
                '$match': {
                    'title': {"$exists": False},
                    'triggered_at': triggered_at
                }
            }
        ]
        cursor = db[read_collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return cursor

    def check_records(self, records, fields, data_range):
        loop_count = 0
        for record in records:
            if loop_count > data_range:
                break
            pprint.pprint([record[field] for field in fields])
            loop_count += 1


if __name__ == '__main__':
    running = {'list': True, 'detail': True, 'check': True}
    data_ranges = {'list': 15, 'detail': 10, 'check': 10}
    check_collection = 'fp_detail'
    check_triggered_by = 'get_' + check_collection
    headers = {
            'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            'x-disco-client-id': 'web'
        }
    fp_list_url = "https://disco.deliveryhero.io/listing/api/v1/pandora/vendors?latitude={latitude}&longitude={longitude}&language_id=6&include=characteristics&dynamic_pricing=0&configuration=Original&country=tw&customer_id=&\
                customer_hash=&budgets=&cuisine=&sort=&food_characteristic=&use_free_delivery_label=false&vertical=restaurants&limit={limit}&offset={offset}&customer_type=regular"
    fp_detail_url = "https://tw.fd-api.com/api/v5/vendors/{uuid}?include=menus&language_id=6&dynamic_pricing=0&opening_type=delivery&order_time={order_time}%2B0800&latitude={latitude}&longitude={longitude}"
    fp_deliver_fee_url = 'https://tw.fd-api.com/api/v5/vendors/{uuid}/delivery-fee?&latitude={latitude}&longitude={longitude}&order_time={order_time}&basket_size=0&basket_currency=$&dynamic_pricing=0'

    if running['list']:
        start = time.time()
        data_range = data_ranges['list']
        list_crawler = FPDinerListCrawler(
            target, fp_list_url, headers, db,
            write_collection='fp_list', offset=0, limit=data_range)
        diners_count_op = list_crawler.main()
        print('This time crawled ', diners_count_op, ' diners.')
        time.sleep(5)
        dispatcher = FPDinerDispatcher(db, read_collection='fp_list', write_collection='fp_list_temp')
        diners_count_ip = dispatcher.main()
        print('There are ', diners_count_ip, ' were latest triggered on fp_list.')
        print("Is dispatcher's input length >= list_crawler's output: ")
        print(diners_count_ip >= diners_count_op)

    if running['detail']:
        start = time.time()
        data_range = data_ranges['detail']
        detail_crawler = FPDinerDetailCrawler(
            target, fp_detail_url, fp_deliver_fee_url, headers, db,
            read_collection='fp_list_temp', write_collection='fp_detail', log_collection='trigger_log',
            triggered_by='get_fp_list', offset=False, limit=data_range)
        diners, error_logs = detail_crawler.main()
        stop = time.time()
        time.sleep(5)
        pprint.pprint(stop - start)

    if running['check']:
        data_range = data_ranges['check']
        checker = FPChecker(db, check_collection, check_triggered_by)
        last_records = checker.get_latest_records(data_range)
        errorlogs = checker.get_latest_errorlogs()
        checker.check_records(last_records, ['title', 'deliver_time', 'triggered_at'], data_range)
        pprint.pprint(list(errorlogs))
