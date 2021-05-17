# for data handling
# import pandas as pd

# for db control
from pymongo import MongoClient

# for crawling from js-website
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# for crawling from html only website
import requests

# for html parsing
# from bs4 import BeautifulSoup
# from lxml import etree

# for powerful dict
# from collections import defaultdict
# from collections import OrderedDict

# for file handling
import os
import sys
# import pickle
import json

# for timing and not to get caught
import time
import random

# for plot
# import seaborn as sns
# import matplotlib.pyplot as plt
# from geopy.distance import distance
from datetime import datetime
# import pprint

from dotenv import load_dotenv

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
    def __init__(self,
                 driver_path='',
                 headless=True,
                 auto_close=True,
                 create_driver=False):
        if create_driver:
            self.driver = self.chrome_create(driver_path, headless, auto_close)

    def chrome_create(self, driver_path, headless=False, auto_close=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        if not auto_close:
            chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option(
            'prefs', {'intl.accept_languages': 'en,en_US'})
        driver = webdriver.Chrome(driver_path, options=chrome_options)
        driver.delete_all_cookies()
        driver.implicitly_wait(2)
        return driver

    def chrome_close(self, driver):
        driver.close()

    def get_diners_info_from_FP_API(self, target):
        print('a')
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
            print(url)
        except Exception:
            error_log = {'error': 'target value wrong'}
            print('target value wrong')
            return False, error_log
        try:
            r = requests.get(url, headers=headers)
        except Exception:
            error_log = {'error': 'vendors_api wrong'}
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
                    'uuid': uuid
                }
                diners_info.append(result)
        except Exception:
            error_log = {'error': 'parse vendors_api response wrong'}
            print('parse vendors_api response wrong')
            return False, error_log
        return diners_info, error_log

    def main(self, target, db, collection):
        diners_info, error_log = self.get_diners_info_from_FP_API(target)
        # print(diners_info, error_log)
        if diners_info:
            record = {'time': datetime.now(), 'data': diners_info}
            db[collection].insert_one(record)
        else:
            # print(diners_info)
            print(error_log['error'])


class FPDinerDetailCrawler():
    def __init__(self, diners_info_collection):
        self.diners_info = self.get_diners_info(diners_info_collection)

    def get_diners_info(self, diners_info_collection):
        pipeline = [
            {'$sort': {'time': -1}},
            {'$group': {
                '_id': '$data',
                'time': {'$last': '$time'}
            }}
        ]
        result = db[diners_info_collection].aggregate(pipeline=pipeline)
        result = list(result)[0]['_id']
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

    def chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def slice_and_save(self, diners_size_bytes, diners, _id, now, error_logs, db, collection):
        chunk_size = diners_size_bytes // 12000000
        data_generator = self.chunks(diners, chunk_size)
        record = {'_id': _id, 'time': now, 'data': [], 'error_logs': error_logs}
        db['test_upsert'].update_one({'time': now}, {'$set': record}, upsert=True)
        for data in data_generator:
            db[collection].update_one({
                '_id': _id,
                '$push': {
                    'data': {
                        '$each': data
                    }
                }})

    def main(self, db, collection, data_range):
        now = datetime.now()
        _id = now.strftime('%Y-%m-%d %H:%M:%S')
        diners, error_logs = self.get_diners_details(data_range=data_range)
        diners_size_bytes = sys.getsizeof(diners)
        if diners_size_bytes > 12000000:
            try:
                self.slice_and_save(diners_size_bytes, diners, _id, now, error_logs, db, collection)
            except Exception:
                print('slice and save wrong')
                return diners, error_logs
        else:
            record = {'time': now, 'data': diners, 'error_logs': error_logs}
            db[collection].insert_one(record)
        return diners, error_logs


if __name__ == '__main__':
    start = time.time()
    d_list_crawler = FPDinerListCrawler()
    d_list_crawler.main(target, db=db, collection='fp_temp')
    stop = time.time()
    print(stop - start)

    d_detail_crawler = FPDinerDetailCrawler('fp_temp')
    start = time.time()
    diners, error_logs = d_detail_crawler.main(db=db, collection='fp_detail', data_range=0)
    stop = time.time()
    print(stop - start)
