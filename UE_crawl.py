# for data handling
# import pandas as pd

# for db control
from pymongo import MongoClient

# for crawling from js-website
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# for crawling from html only website
import requests

# for html parsing
# from bs4 import BeautifulSoup
from lxml import etree

# for powerful dict
# from collections import defaultdict
# from collections import OrderedDict

# for file handling
import os
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
import pprint

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

target = {'name': 'Appworks School', 'address': '110台北市信義區基隆路一段178號', 'gps': (25.0424488, 121.562731)}
db = admin_client['ufc_temp']
driver_path = os.getenv("DRIVER_PATH")


class UEDinerListCrawler():
    def __init__(self, driver_path, headless, auto_close, inspect):
        self.driver = self.chrome_create(driver_path, headless, auto_close, inspect)

    def chrome_create(self, driver_path, headless=False, auto_close=False, inspect=False):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        if not auto_close:
            chrome_options.add_experimental_option("detach", True)
        if inspect:
            chrome_options.add_argument("--auto-open-devtools-for-tabs")
        chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
        driver = webdriver.Chrome(driver_path, options=chrome_options)
        driver.delete_all_cookies()
        driver.implicitly_wait(2)
        return driver

    def chrome_close(self, driver):
        driver.close()

    def send_location_to_UE(self, target, html_collection, responses_collection):
        error_log = {}
        start = time.time()
        driver = self.driver
        driver.get('https://www.ubereats.com/tw')
        try:
            driver.find_element_by_xpath('//*[@id="location-typeahead-home-input"]').send_keys(target['address'])
        except Exception:
            error_log = {'error': 'send location wrong'}
            return False, False, error_log
        time.sleep(3)
        try:
            try:
                driver.find_element_by_xpath('//button[.="Find Food"]').click()
                lang = 'en'
            except Exception:
                driver.find_element_by_xpath('//button[.="尋找食物"]').click()
                lang = 'zh'
        except Exception:
            error_log = {'error': 'send location wrong'}
            return False, False, error_log
        time.sleep(3)
        if lang == 'en':
            locator_xpath = '//button[text() = "Show more"]'
            locator = (By.XPATH, '//button[text() = "Show more"]')
        elif lang == 'zh':
            locator_xpath = '//button[text() = "顯示更多餐廳"]'
            locator = (By.XPATH, '//button[text() = "顯示更多餐廳"]')
        try:
            while len(driver.find_elements_by_xpath(locator_xpath)) > 0:
                WebDriverWait(driver, 30, 0.5).until(EC.presence_of_element_located(locator))
                driver.find_element_by_xpath(locator_xpath).send_keys(Keys.ENTER)
                try:
                    WebDriverWait(driver, 30, 0.5).until(EC.presence_of_element_located(locator))
                except Exception:
                    break
        except Exception:
            error_log = {'error': 'scroll wrong'}
            return False, False, error_log
        html = driver.page_source
        self.save_html_to_mongo(html, error_log, html_collection)
        selector = etree.HTML(html)
        dict_response, error_log = self.get_diners_response(driver, responses_collection)
        self.save_responses_to_mongo(error_log, responses_collection)
        # self.driver.close()
        stop = time.time()
        print(stop - start)
        return selector, dict_response, error_log

    def save_html_to_mongo(self, html, error_log, collection):
        record = {'time': datetime.now(), 'html': html, 'error_log': error_log}
        db[collection].insert_one(record)

    def save_responses_to_mongo(self, error_log, collection):
        record = {'time': datetime.now(), 'error_log': error_log}
        db[collection].insert_one(record)

    def get_diners_response(self, driver=None, responses_collection='responses_collection'):
        if not driver:
            driver = self.driver
        error_log = {}
        responses = []
        raw_responses = []
        start = time.time()
        try:
            for request in driver.requests:
                if request.url == 'https://www.ubereats.com/api/getFeedV1?localeCode=tw':
                    raw_responses.append(json.loads(request.response.body))
                    diners = json.loads(request.response.body)['data']['feedItems']
                    if diners == []:
                        continue
                    elif diners[0]['type'] == 'STORE':
                        diners = json.loads(request.response.body)['data']['storesMap']
                    try:
                        response = self.get_diner_response(diners)
                        responses.extend(response)
                    except Exception:
                        error_log = {'error': 'parse selenium response wrong'}
                        return False, error_log
        except Exception:
            error_log = {'error': 'get selenium response wrong'}
            return False, error_log
        stop = time.time()
        print(stop - start)
        responses = list(set(responses))
        dict_response = {i[0]: i[1] for i in responses}
        return dict_response, error_log

    def get_diner_response(self, diners):
        results = []
        if type(diners) == list:
            for diner in diners:
                try:
                    if diner['analyticsLabel'] == 'store_front':
                        uuid = diner['uuid']
                        title = diner['store']['title']['text']
                        results.append((title, uuid))
                    else:
                        pass
                except Exception:
                    pprint.pprint(diner)
        elif (type(diners) == dict) & (diners != {}):
            for uuid in diners:
                title = diners[uuid]['title']
                results.append((title, uuid))
        return results

    def get_diner_divs(self, selector):
        diner_divs = selector.xpath('''
            //main[@id="main-content"]/div[position()=last()]/div[position()=last()]/div[position()=last()]\
            /div[position()=last()]/div[position()=last()]/div
            ''')
        print(len(diner_divs))
        return diner_divs

    def get_diner_info(self, diner_div):
        link = diner_div.xpath('.//a')[0].get('href')
        link = 'https://www.ubereats.com' + link
        title = str(diner_div.xpath('.//h3/text()')[0])
        try:
            diner_div.xpath(".//img[@src='https://d4p17acsd5wyj.cloudfront.net/eatsfeed/other_icons/top_eats.png']")[0]
            UE_choice = 1
        except Exception:
            UE_choice = 0
        if diner_div.xpath(".//span[contains(.,'費用')]/text()") == []:
            deliver_fee = 0
        else:
            deliver_fee = diner_div.xpath(".//span[contains(.,'費用')]/text()")[0]
        if diner_div.xpath(".//div[contains(.,'分鐘')]/text()") == []:
            deliver_time = 0
        else:
            deliver_time = diner_div.xpath(".//*[contains(.,'分鐘')]/text()")[0]
        diner = {
            'title': title,
            'link': link,
            'deliver_fee': deliver_fee,
            'deliver_time': deliver_time,
            'UE_choice': UE_choice,
        }
        return diner

    def combine_uuid_diners_info(self, diners_info, dict_response):
        for diner in diners_info:
            diner['uuid'] = dict_response[diner['title']]
        return diners_info
    
    def main(self, target, db, html_collection, responses_collection, info_collection):
        selector, dict_response, error_log = self.send_location_to_UE(target, html_collection=html_collection, responses_collection=responses_collection)
        if (type(selector) != bool) and dict_response:
            diner_divs = self.get_diner_divs(selector)
            diners_info = [self.get_diner_info(i) for i in diner_divs]
            diners_info = self.combine_uuid_diners_info(diners_info, dict_response)
            record = {'time': datetime.now(), 'data': diners_info}
            db[info_collection].insert_one(record)
        else:
            print(error_log['error'])

class UEDinerDetailCrawler():
    def __init__(self, info_collection):
        self.diners_info = self.get_diners_info(info_collection)

    def get_diners_info(self, info_collection):
        pipeline = [
            {'$sort': {'time': -1}},
            {'$group': {
                '_id': '$data',
                'time': {'$last': '$time'}
            }}
        ]
        result = db[info_collection].aggregate(pipeline=pipeline)
        result = list(result)[0]['_id']
        return result

    def get_diner_detail_from_UE_API(self, diner):
        error_log = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            'origin': 'https://www.ubereats.com',
            'x-csrf-token': 'x',
            'authority': 'www.ubereats.com',
            'accept': '*/*',
            'citySlug': "taipei",
            'content-type': 'application/json',
            'cookie': '''uev2.loc=%7B%22address%22%3A%7B%22address1%22%3A%22AppWorks%20School%22%2C%22address2%22%3A%22%E5%9F%BA%E9%9A%86%E8%B7%AF%E4%B8%80%E6%AE%B5178%E8%99%9F%2C%20%E5%8F%B0%E5%8C%97%E5%B8%82%E4%BF%A1%E7%BE%A9%E5%8D%80%22%2C%22\
                aptOrSuite%22%3A%22%22%2C%22eaterFormattedAddress%22%3A%22110%E5%8F%B0%E7%81%A3%E5%8F%B0%E5%8C%97%E5%B8%82%E4%BF%A1%E7%BE%A9%E5%8D%80%E5%9F%BA%E9%9A%86%E8%B7%AF%E4%B8%80%E6%AE%B5178%E8%99%9F%22%2C%22subtitle%22%3A%22%E5%9F%BA%E9%9A%\
                    86%E8%B7%AF%E4%B8%80%E6%AE%B5178%E8%99%9F%2C%20%E5%8F%B0%E5%8C%97%E5%B8%82%E4%BF%A1%E7%BE%A9%E5%8D%80%22%2C%22title%22%3A%22AppWorks%20School%22%2C%22uuid%22%3A%22%22%7D%2C%22latitude%22%3A25.042416%2C%22longitude%22%3A121.\
                        56506%2C%22reference%22%3A%22ChIJg0OvDk-rQjQRGMdB-Cq3egk%22%2C%22referenceType%22%3A%22google_places%22%2C%22type%22%3A%22google_places%22%2C%22source%22%3A%22manual_auto_complete%22%2C%22addressComponents%22%3A%7B%\
                            22countryCode%22%3A%22TW%22%2C%22firstLevelSubdivisionCode%22%3A%22%E5%8F%B0%E5%8C%97%E5%B8%82%22%2C%22city%22%3A%22%E4%BF%A1%E7%BE%A9%E5%8D%80%22%2C%22postalCode%22%3A%22110%22%7D%2C%22originType%22%3A%22\
                                user_autocomplete%22%7D'''
            }
        try:
            payload = {
                'storeUuid': diner['uuid'],
                'sfNuggetCount': 1  # clicked how many stores in this session
            }
        except Exception:
            error_log = {'error': 'diner_info wrong', 'diner': diner}
            return False, error_log
        url = 'https://www.ubereats.com/api/getStoreV1?localeCode=tw'
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload))
            UE_API_response = json.loads(r.content)['data']
        except Exception:
            error_log = {'error': 'store_api wrong', 'diner': diner}
            return False, error_log
        diner = self.clean_UE_API_response(UE_API_response, diner)
        time.sleep(1)
        return diner, error_log

    def get_diners_details(self, data_range=0):
        if data_range == 0:
            diners_info = self.diners_info
        else:
            diners_info = self.diners_info[:data_range]
        diners = []
        error_logs = []
        loop_count = 0
        for diner in diners_info:
            diner, error_log = self.get_diner_detail_from_UE_API(diner)
            if diner:
                diners.append(diner)
            if error_log != {}:
                error_logs.append(error_log)
            loop_count += 1
            if loop_count % 500 == 0:
                time.sleep(random.randint(10, 30))
        return diners, error_logs

    def clean_UE_API_response(self, UE_API_response, diner):
        error_log = {}
        try:
            diner = self.get_diner_menu(UE_API_response, diner)
        except Exception:
            error_log = {'error': 'get menu wrong', 'diner': diner['uuid']}
            return False, error_log
        try:
            diner = self.get_open_hours(UE_API_response, diner)
        except Exception:
            error_log = {'error': 'get open hours wrong', 'diner': diner['uuid']}
            return False, error_log
        try:
            diner = self.get_other_info(UE_API_response, diner)
        except Exception:
            error_log = {'error': 'get other info wrong', 'diner': diner['uuid']}
            return False, error_log
        return diner, error_log

    def get_other_info(self, UE_API_response, diner):
        diner['deliver_time'] = UE_API_response['etaRange']
        if not diner['deliver_time']:
            diner['deliver_time'] = 0
        diner['deliver_fee'] = UE_API_response['fareBadge']
        if not diner['deliver_fee']:
            diner['deliver_fee'] = 0
        diner['budget'] = len(UE_API_response['priceBucket'])
        try:
            diner['rating'] = UE_API_response['rating']['ratingValue']
            diner['view_count'] = int(UE_API_response['rating']['reviewCount'])
        except Exception:
            diner['rating'] = 0
            diner['view_count'] = 0
        # food_characteristics = [i['name'] for i in FP_API_response['food_characteristics']]
        # cuisines = [i['name'] for i in FP_API_response['cuisines']]
        diner['tags'] = UE_API_response['cuisineList']
        location_infos = UE_API_response['location']
        diner['address'] = location_infos['streetAddress']
        diner['gps'] = (location_infos['latitude'], location_infos['latitude'])
        return diner

    def get_diner_menu(self, UE_API_response, diner):
        menu = []
        sections = UE_API_response['sections']
        subsections_map = UE_API_response['subsectionsMap']
        items_map = UE_API_response['sectionEntitiesMap']
        for section in sections:
            section_uuid = section['uuid']
            section_title = section['title']
            for subsection_id in section['subsectionUuids']:
                items_uuid = subsections_map[subsection_id]['itemUuids']
                subsection_title = subsections_map[subsection_id]['title']
                items_list = []
                for item_uuid in items_uuid:
                    keys = items_map[section_uuid][item_uuid].keys()
                    if 'description' in keys:
                        item_description = items_map[section_uuid][item_uuid]['description']
                        item_description = item_description.replace('\\n', '')
                    else:
                        item_description = ''
                    item_price = items_map[section_uuid][item_uuid]['price'] // 100
                    item_title = items_map[section_uuid][item_uuid]['title']
                    item_image_url = items_map[section_uuid][item_uuid]['imageUrl']
                    items_list.append({
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

    def get_open_hours(self, UE_API_response, diner):
        business_hours = UE_API_response['hours']
        open_hours = []
        day_map = {
            '星期一': 'Mon.', '周一': 'Mon.', '週一': 'Mon.',
            '星期二': 'Tue.', '周二': 'Tue.', '週二': 'Tue.',
            '星期三': 'Wed.', '周三': 'Wed.', '週三': 'Wed.',
            '星期四': 'Thu.', '周四': 'Thu.', '週四': 'Thu.',
            '星期五': 'Fri.', '周五': 'Fri.', '週五': 'Fri.',
            '星期六': 'Sat.', '周六': 'Sat.', '週六': 'Sat.',
            '星期日': 'Sun.', '周日': 'Sun.', '週日': 'Sun.',
        }
        days = ['Mon.', 'Tue.', 'Wed.', 'Thu.', 'Fri.', 'Sat.', 'Sun.']
        for hours in business_hours:
            day_range = hours['dayRange']
            stop_day = None
            if ' - ' in day_range:
                day_ranges = day_range.split(' - ')
                start_day = day_ranges[0]
                stop_day = day_ranges[1]
                start_day = day_map[start_day]
                stop_day = day_map[stop_day]
            elif '每天' == day_range:
                start_day = 'Mon.'
                stop_day = 'Sun.'
            else:
                start_day = day_range
                start_day = day_map[start_day]
            start_day_index = days.index(start_day)
            if stop_day:
                stop_day_index = days.index(stop_day)
                if start_day_index > stop_day_index:
                    run_days = days[start_day_index:] + days[:stop_day_index]
                else:
                    run_days = days[start_day_index: stop_day_index+1]
            else:
                run_days = [start_day]            
            for sectionHour in hours['sectionHours']:
                start_minute = int(((sectionHour['startTime'] / 60) % 1) * 60)
                start_hour = sectionHour['startTime'] // 60
                stop_minute = int(round(((sectionHour['endTime'] / 60) % 1) * 60, 0))
                stop_hour = sectionHour['endTime'] // 60
                if len(str(start_minute)) == 1:
                    start_minute = '0' + str(start_minute)
                else:
                    start_minute = str(start_minute)
                if len(str(stop_minute)) == 1:
                    stop_minute = '0' + str(stop_minute)
                else:
                    stop_minute = str(stop_minute)
                for run_day in run_days:
                    open_hour = (run_day, f'{start_hour}:{start_minute}', f'{stop_hour}:{stop_minute}')
                    open_hours.append(open_hour)
        diner['open_hours'] = open_hours
        return diner
    
    def main(self, db, collection, data_range=0):
        diners, error_logs = self.get_diners_details(data_range=data_range)
        record = {'time': datetime.now(), 'data': diners, 'error_logs': error_logs}
        db[collection].insert_one(record)
        return diners, error_logs