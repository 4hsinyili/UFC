# for data handling
# import pandas as pd

# for db control
from pymongo import MongoClient

# for crawling from js-website
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# for crawling from html only website
# import requests

# for html parsing
# from bs4 import BeautifulSoup
from lxml import etree

# for powerful dict
# from collections import defaultdict
# from collections import OrderedDict

# for file handling
import os
# import pickle
# import json

# for timing and not to get caught
import time
# import random

# for plot
# import seaborn as sns
# import matplotlib.pyplot as plt
# from geopy.distance import distance
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
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

targets = [{
    'name': '五之神製作所 台灣',
    'address': '110台北市信義區忠孝東路四段553巷6弄6號',
    'gps': (25.0424644, 121.5626151)
}, {
    'name': '一蘭 台灣台北別館',
    'address': '110台北市信義區松壽路11號 B1F',
    'gps': (25.0363184, 121.5629489)
}, {
    'name': '太陽蕃茄拉麵 誠品信義店',
    'address': '110台北市信義區松高路11號B2',
    'gps': (25.0363184, 121.5629489)
}]
db = admin_client['ufc_temp']
driver_path = os.getenv("DRIVER_PATH")


class GMCrawler():
    def __init__(self, driver_path, headless, auto_close, inspect):
        self.driver = self.chrome_create(driver_path, headless, auto_close,
                                         inspect)

    def chrome_create(self,
                      driver_path,
                      headless=False,
                      auto_close=False,
                      inspect=False):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        if not auto_close:
            chrome_options.add_experimental_option("detach", True)
        if inspect:
            chrome_options.add_argument("--auto-open-devtools-for-tabs")
        chrome_options.add_experimental_option(
            'prefs', {'intl.accept_languages': 'en,en_US'})
        driver = webdriver.Chrome(driver_path, options=chrome_options)
        driver.delete_all_cookies()
        driver.implicitly_wait(2)
        return driver

    def chrome_close(self, driver):
        driver.close()

    def get_link(self, target):
        error_log = {}
        driver = self.driver
        try:
            driver.get('https://www.google.com.tw/maps')
            driver.find_element_by_xpath(
                '//input[@id="searchboxinput"]').send_keys(target['address'] +
                                                           target['name'])
            driver.find_element_by_xpath(
                '//button[@id="searchbox-searchbutton"]').click()
            time.sleep(4)
            if driver.current_url == 'https://www.google.com.tw/maps':
                time.sleep(4)
            time.sleep(3)
        except Exception:
            error_log = {'error': 'get place link wrong', 'diner': target}
            return False, error_log
        # print(driver.current_url)
        diner = {
            'title': target['name'],
            'address': target['address'],
            'link': driver.current_url
        }
        return diner, error_log

    def get_info(self, diner):
        error_log = {}
        driver = self.driver
        html = driver.page_source
        selector = etree.HTML(html)
        try:
            rating = float(
                selector.xpath(
                    '//span[@class="mapsConsumerUiSubviewSectionSharedStar__section-star-display"]/text()'
                )[0])
            view_button = selector.xpath(
                '//span[@class="mapsConsumerUiSubviewSectionRating__reviews-tap-area mapsConsumerUiSubviewSectionRating__reviews-tap-area-enabled"]/span/button'
            )[0]
            view_count = view_button.xpath('./text()')[0]
            view_count = view_count.split('則評論')[0]
            view_count = view_count.replace(',', '').replace(' ', '')
            budget = selector.xpath('//span[contains(., "$")]/text()')[0]
        except Exception:
            error_log = {'error': 'get place info wrong', 'diner': diner}
            return False, error_log
        try:
            driver.find_element_by_xpath(
                '//span[@class="mapsConsumerUiSubviewSectionRating__reviews-tap-area mapsConsumerUiSubviewSectionRating__reviews-tap-area-enabled"]/span/button'
            ).click()
            time.sleep(3.5)
        except Exception:
            error_log = {
                'error': 'get place review page wrong',
                'diner': diner
            }
            return False, error_log
        try:
            pane = driver.find_element_by_xpath(
                '//div[@class="section-layout section-scrollbox mapsConsumerUiCommonScrollable__scrollable-y mapsConsumerUiCommonScrollable__scrollable-show"]'
            )
            for _ in range(3):
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", pane)
                time.sleep(3.5)
        except Exception:
            error_log = {'error': 'scroll review page wrong', 'diner': diner}
            return False, error_log
        try:
            show_all = driver.find_elements_by_xpath(
                '//button[@aria-label="顯示更多"]')
            for button in show_all:
                button.click()
        except Exception:
            error_log = {'error': 'click all review wrong', 'diner': diner}
            return False, error_log
        html = driver.page_source
        selector = etree.HTML(html)
        diner['rating'] = rating
        diner['view_count'] = view_count
        diner['budget'] = budget
        return selector, diner

    def get_reviews(self, selector, diner):
        error_log = {}
        try:
            names = selector.xpath(
                '//div[@aria-label="所有評論"]/div[position()=last()]/div[position()=last()-1]/div[@class="section-review mapsConsumerUiCommonRipple__ripple-container gm2-body-2"]/@aria-label'
            )
            raw_rating = selector.xpath(
                '//div[@aria-label="所有評論"]/div[position()=last()]/div[position()=last()-1]/div[@class="section-review mapsConsumerUiCommonRipple__ripple-container gm2-body-2"]//span[@class="section-review-stars"]/@aria-label'
            )
            ratings = [
                int(i.replace(' ', '').split('顆星')[0]) for i in raw_rating
            ]
            raw_dates = selector.xpath(
                '//div[@aria-label="所有評論"]/div[position()=last()]/div[position()=last()-1]/div[@class="section-review mapsConsumerUiCommonRipple__ripple-container gm2-body-2"]//span[@class="section-review-publish-date"]/text()'
            )
        except Exception:
            error_log = {'error': 'get review metadata wrong', 'diner': diner}
            return False, error_log
        try:
            dates = []
            today = datetime.now().date()
            for raw_date in raw_dates:
                scope = raw_date.split(' ')[1]
                delta = int(raw_date[0])
                try:
                    if '天' in scope:
                        date = today.replace(day=(today.day - delta))
                    elif '月' in scope:
                        date = today - relativedelta(months=delta)
                    elif '週' in scope:
                        date = today - timedelta(weeks=delta)
                    elif '年' in scope:
                        date = today.replace(year=(today.year - delta))
                except Exception:
                    index = raw_dates.index(raw_date)
                    print(index, names[index], raw_date)
                    date = today
                date_time = datetime.combine(date, datetime.min.time())
                dates.append(date_time)
        except Exception:
            error_log = {'error': 'parse review date wrong', 'diner': diner}
            return False, error_log
        try:
            raw_content = selector.xpath(
                '//div[@aria-label="所有評論"]/div[position()=last()]/div[position()=last()-1]/div[@class="section-review mapsConsumerUiCommonRipple__ripple-container gm2-body-2"]//span[@class="section-review-text"]/text()'
            )
            content = [
                i.replace("\n",
                          '').replace('\u2028',
                                      '').replace('\u2029',
                                                  '').replace('\uFEFF', '')
                for i in raw_content
            ]
        except Exception:
            error_log = {'error': 'parse review content wrong', 'diner': diner}
            return False, error_log
        indexes = range(len(names))
        reviews = [{
            'name': names[i],
            'rating': ratings[i],
            'date': dates[i],
            'review': content[i]
        } for i in indexes]
        diner['reviews'] = reviews
        return diner, error_log

    def main(self, targets, db, collection):
        diners = []
        error_logs = []
        for target in targets:
            # start = time.time()
            diner, error_log = self.get_link(target)
            if diner:
                selector, diner = self.get_info(diner)
                diner, error_log = self.get_reviews(selector, diner)
                diners.append(diner)
                if error_log == {}:
                    pass
                else:
                    error_logs.append(error_log)
            else:
                print('error while try to get ', target['name'], "'s link.")
                error_log = {
                    'error': "error while try to get link",
                    'diner': target
                }
                error_logs.append(error_log)
            # stop = time.time()
            # print('each site: ', stop - start)
        self.chrome_close()
        record = {
            'time': datetime.now(),
            'data': diners,
            'error_logs': error_logs
        }
        db[collection].insert_one(record)
        return diners, error_logs


class GMChecker():
    def __init__(self, db, collection, pipeline):
        self.db = db
        self.collection = collection
        self.pipeline = pipeline

    def get_last_record(self):
        db = self.db
        collection = self.collection
        pipeline = self.pipeline
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        result = list(result)[0]['_id']
        return result


if __name__ == '__main__':
    # start = time.time()
    # link_crawler = GMCrawler(driver_path=driver_path,
    #                          headless=True,
    #                          auto_close=True,
    #                          inspect=False)
    # diners, error_logs = link_crawler.main(targets,
    #                                        db=db,
    #                                        collection='gm_reviews')
    # stop = time.time()
    # print(stop - start)
    pipeline = [
        {'$sort': {'time': -1}},
        {'$group': {
            '_id': '$data',
            'time': {'$last': '$time'}
        }}, {
            '$limit': 1
        }
    ]
    checker = GMChecker(db, 'gm_reviews', pipeline)
    last_record = checker.get_last_record()
    pprint.pprint(last_record[0])
