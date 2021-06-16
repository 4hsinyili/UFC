# for db control
from pymongo import MongoClient, UpdateOne

# for crawling from API
import requests

# for file handling
import json
import env
import configparser

# for timing and not to get caught
import time
import random
from datetime import datetime

# for preview
import pprint

# home-made modules
from Crawlers import utils

MONGO_EC2_URI = env.MONGO_EC2_URI

CONFIG = configparser.ConfigParser()
CONFIG.read('crawler.conf')
DB_NAME = CONFIG['Local']['db_name']
LIST_COLLECTION = CONFIG['Collections']['fp_list']
LIST_TEMP_COLLECTION = CONFIG['Collections']['fp_list_temp']
DETAIL_COLLECTION = CONFIG['Collections']['fp_detail']
LOG_COLLECTION = CONFIG['Collections']['trigger_log']
GET_FP_LIST = CONFIG['TriggeredBy']['get_fp_list']
GET_FP_DETAIL = CONFIG['TriggeredBy']['get_fp_detail']

API_JSON = utils.read_json('api_fp.json')
HEADERS = API_JSON['headers']
LIST_URL = API_JSON['list_url']
DETAIL_URL = API_JSON['detail_url']
DELIVER_FEE_URL = API_JSON['deliver_fee_url']
TARGET = utils.read_json('target_fp.json')

admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client[DB_NAME]


class FPDinerListCrawler():
    def __init__(self, target, fp_list_url, headers, db, write_collection,
                 log_collection, w_triggered_by, offset, limit):
        self.target = target
        self.headers = headers
        self.db = db
        self.write_collection = write_collection
        self.log_collection = log_collection
        self.w_triggered_by = w_triggered_by
        self.fp_list_url = fp_list_url
        self.offset = offset
        self.limit = limit
        self.end_point = self.generate_fp_list_endpoint()
        self.triggered_at = utils.generate_triggered_at()

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

    def parse_diners(self, diners):
        data = []
        for diner in diners:
            link = diner['redirection_url']
            title = diner['name']
            uuid = diner['code']
            choice = int(diner['is_best_in_city'])
            deliver_fee = diner['minimum_delivery_fee']
            deliver_time = diner['minimum_delivery_time']
            result = {
                'title': title,
                'link': link,
                'deliver_fee': deliver_fee,
                'deliver_time': deliver_time,
                'choice': choice,
                'uuid': uuid,
                'triggered_at': self.triggered_at
            }
            data.append(result)
        return data

    def get_diners_info_from_fp(self, target):
        triggered_at = self.triggered_at
        print('Start getting diners list of ', target['title'], 'begin at',
              triggered_at, '.')
        error_log = {}

        try:
            end_point = self.end_point
        except Exception:
            error_log = {
                'error': 'target value wrong',
                'triggered_at': triggered_at
            }
            print('target value wrong')
            return False, error_log

        try:
            list_response = requests.get(end_point, headers=self.headers)
        except Exception:
            error_log = {
                'error': 'vendors_api wrong',
                'triggered_at': triggered_at
            }
            print('vendors_api wrong')
            return False, error_log

        try:
            list_ = json.loads(list_response.content)
            diners = list_['data']['items']
            diners_info = self.parse_diners(diners)
        except Exception:
            error_log = {
                'error': 'parse vendors_api response wrong',
                'triggered_at': triggered_at
            }
            print('parse vendors_api response wrong')
            return False, error_log, triggered_at

        return diners_info, error_log

    def main(self):
        start = time.time()
        db = self.db
        write_collection = self.write_collection
        target = self.target
        self.batch_id = utils.save_start_at(self)

        diners_info, error_log = self.get_diners_info_from_fp(target)
        print('There are ', len(diners_info), ' diners successfully paresed.')

        if error_log == {}:
            pass
        else:
            db[write_collection].insert_one(error_log)

        if diners_info:
            records = [
                UpdateOne(
                    {
                        'uuid': record['uuid'],
                        'triggered_at': record['triggered_at']
                    }, {'$setOnInsert': record},
                    upsert=True) for record in diners_info
            ]
            db[write_collection].bulk_write(records)
            utils.save_triggered_at(self, records_count=len(diners_info))
        else:
            pprint.pprint('Error Logs:')
            pprint.pprint(error_log)

        stop = time.time()
        print('Get diner list near ', target['title'], ' took ', stop - start,
              ' seconds.')

        return len(diners_info)


class FPDinerDetailCrawler():
    def __init__(self,
                 target,
                 fp_detail_url,
                 fp_deliver_fee_url,
                 headers,
                 db,
                 read_collection,
                 write_collection,
                 log_collection,
                 r_triggered_by,
                 w_triggered_by,
                 offset=0,
                 limit=0):
        self.target = target
        self.headers = headers
        self.fp_detail_url = fp_detail_url
        self.fp_deliver_fee_url = fp_deliver_fee_url
        self.db = db
        self.read_collection = read_collection
        self.write_collection = write_collection
        self.log_collection = log_collection
        self.r_triggered_by = r_triggered_by
        self.w_triggered_by = w_triggered_by
        self.triggered_at, self.batch_id = utils.get_pre_run_info(self)
        self.diners_cursor = utils.get_diners_cursor(self, offset, limit)
        self.order_time = self.generate_order_time()

    def generate_order_time(self):
        now = datetime.utcnow()
        if now.hour + 8 < 24:
            order_time = now.replace(hour=(now.hour +
                                           8)).strftime('%Y-%m-%dT%H:%M:%S')
        else:
            order_time = now.replace(day=(now.day + 1),
                                     hour=(now.hour -
                                           16)).strftime('%Y-%m-%dT%H:%M:%S')
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

    def get_diners_detail(self):
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
        print('There are ', len(diners_info),
              ' diners able to send to Appworks School.')
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
            error_log = {
                'error': 'get open hours wrong',
                'diner': diner['uuid']
            }
            return False, error_log
        try:
            diner = self.get_other_info(detail, diner)
        except Exception:
            error_log = {
                'error': 'get other info wrong',
                'diner': diner['uuid']
            }
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
        diner['gps'] = (detail['latitude'], detail['longitude'])
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

    def save_records(self, diners):
        write_collection = self.write_collection
        records = []
        for diner in diners:
            if diner:
                record = UpdateOne(
                    {
                        'uuid': diner['uuid'],
                        'triggered_at': diner['triggered_at']
                    }, {'$setOnInsert': diner},
                    upsert=True)
                records.append(record)
        db[write_collection].bulk_write(records)
        return len(records)

    def main(self):
        db = self.db
        write_collection = self.write_collection
        triggered_at = self.triggered_at

        start = time.time()
        diners, error_logs = self.get_diners_detail()
        if error_logs == []:
            pass
        else:
            db[write_collection].insert_one({
                'uuid': '',
                'triggered_at': triggered_at,
                'error_logs': error_logs
            })
        if diners:
            diners_count = self.save_records(diners)
        else:
            pprint.pprint('Error Logs:')
            pprint.pprint(error_logs)
        stop = time.time()
        if diners:
            print('Get ', diners_count, ' diner detail took ', stop - start,
                  ' seconds.')
            utils.save_triggered_at(self, records_count=diners_count)
        return diners, error_logs


if __name__ == '__main__':
    running = {'list': False, 'detail': False, 'check': True}
    data_ranges = {'list': 15, 'detail': 10, 'check': 10}
    check_collection = DETAIL_COLLECTION
    check_triggered_by = 'get_' + check_collection

    if running['list']:
        start = time.time()
        data_range = data_ranges['list']
        list_crawler = FPDinerListCrawler(TARGET,
                                          LIST_URL,
                                          HEADERS,
                                          db,
                                          write_collection=LIST_COLLECTION,
                                          log_collection=LOG_COLLECTION,
                                          w_triggered_by=GET_FP_LIST,
                                          offset=0,
                                          limit=data_range)
        diners_count_op = list_crawler.main()
        print('This time crawled ', diners_count_op, ' diners.')
        time.sleep(5)
        dispatcher = utils.DinerDispatcher(
            db,
            read_collection=LIST_COLLECTION,
            write_collection=LIST_TEMP_COLLECTION,
            log_collection=LOG_COLLECTION,
            r_triggered_by=GET_FP_LIST,
            limit=data_range)
        diners_count_ip = dispatcher.main()
        print('There are ', diners_count_ip,
              ' were latest triggered on fp_list.')
        print("Is dispatcher's input length >= list_crawler's output: ")
        print(diners_count_ip >= diners_count_op)

    if running['detail']:
        start = time.time()
        data_range = data_ranges['detail']
        detail_crawler = FPDinerDetailCrawler(
            TARGET,
            DETAIL_URL,
            DELIVER_FEE_URL,
            HEADERS,
            db,
            read_collection=LIST_TEMP_COLLECTION,
            write_collection=DETAIL_COLLECTION,
            log_collection=LOG_COLLECTION,
            r_triggered_by=GET_FP_LIST,
            w_triggered_by=GET_FP_DETAIL,
            offset=0,
            limit=data_range)
        diners, error_logs = detail_crawler.main()
        stop = time.time()
        time.sleep(5)
        pprint.pprint(stop - start)

    if running['check']:
        data_range = data_ranges['check']
        checker = utils.Checker(db, read_collection=check_collection, log_collection=LOG_COLLECTION, r_triggered_by=check_triggered_by)
        latest_records_count = checker.get_latest_records_count()
        print(latest_records_count)
        cursor = checker.get_latest_records_cursor(data_range)
        errorlogs = checker.get_latest_errorlogs()
        pprint.pprint(list(errorlogs))
        checker.check_records(cursor,
                              ['title', 'deliver_time', 'triggered_at'],
                              data_range)
