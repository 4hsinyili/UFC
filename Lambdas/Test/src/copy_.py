#  for db control
from pymongo import MongoClient, UpdateOne

# for crawling from js-website
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from lxml import etree

# for file handling
import os
from dotenv import load_dotenv
import json

# for timing and not to get caught
import time
from datetime import datetime

# for preview
import pprint
import sys
print(sys.version)
load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT"))
MONGO_ADMIN_USERNAME = os.getenv("MONGO_ADMIN_USERNAME")
MONGO_ADMIN_PASSWORD = os.getenv("MONGO_ADMIN_PASSWORD")

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)

target = {
    'name': 'Appworks School',
    'address': '110台北市信義區基隆路一段178號',
    'gps': (25.0424488, 121.562731)
}
db = admin_client['ufc_temp']


class UEDinerListCrawler():
    def __init__(self):
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1280x1696')
        chrome_options.add_argument('--user-data-dir=/tmp/user-data')
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.add_argument('--v=99')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--data-path=/tmp/data-path')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--homedir=/tmp')
        chrome_options.add_argument('--disk-cache-dir=/tmp/cache-dir')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
        chrome_options.binary_location = os.getcwd() + "/bin/headless-chromium"
        self.driver = webdriver.Chrome(chrome_options=chrome_options)

    def chrome_close(self, driver):
        driver.close()

    def send_location_to_UE(self, target, html_collection,
                            responses_collection):
        now = datetime.now()
        triggered_at = datetime.combine(now.date(), datetime.min.time())
        triggered_at = triggered_at.replace(hour=now.hour)
        print(target)
        print(triggered_at)
        error_log = {}
        start = time.time()
        driver = self.driver
        driver.get('https://www.ubereats.com/tw')
        try:
            driver.find_element_by_xpath(
                '//*[@id="location-typeahead-home-input"]').send_keys(
                    target['address'])
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
                WebDriverWait(driver, 30, 0.5).until(
                    EC.presence_of_element_located(locator))
                driver.find_element_by_xpath(locator_xpath).send_keys(
                    Keys.ENTER)
                try:
                    WebDriverWait(driver, 30, 0.5).until(
                        EC.presence_of_element_located(locator))
                except Exception:
                    break
        except Exception:
            error_log = {'error': 'scroll wrong'}
            return False, False, error_log
        html = driver.page_source
        self.save_html_to_mongo(html, error_log, html_collection, triggered_at)
        selector = etree.HTML(html)
        dict_response, error_log = self.get_diners_response(
            driver, responses_collection)
        self.save_responses_to_mongo(error_log, responses_collection, triggered_at)
        # self.driver.close()
        stop = time.time()
        print(stop - start)
        return selector, dict_response, error_log, triggered_at

    def save_html_to_mongo(self, html, error_log, collection, triggered_at):
        record = {'triggered_at': triggered_at, 'html': html, 'error_log': error_log}
        db[collection].insert_one(record)

    def save_responses_to_mongo(self, error_log, collection, triggered_at):
        record = {'triggered_at': triggered_at, 'error_log': error_log}
        db[collection].insert_one(record)

    def get_diners_response(self,
                            driver=None,
                            responses_collection='responses_collection'):
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
                    diners = json.loads(
                        request.response.body)['data']['feedItems']
                    if diners == []:
                        continue
                    elif diners[0]['type'] == 'STORE':
                        diners = json.loads(
                            request.response.body)['data']['storesMap']
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

    def get_diner_info(self, diner_div, triggered_at):
        link = diner_div.xpath('.//a')[0].get('href')
        link = 'https://www.ubereats.com' + link
        title = str(diner_div.xpath('.//h3/text()')[0])
        try:
            diner_div.xpath(
                ".//img[@src='https://d4p17acsd5wyj.cloudfront.net/eatsfeed/other_icons/top_eats.png']"
            )[0]
            UE_choice = 1
        except Exception:
            UE_choice = 0
        if diner_div.xpath(".//span[contains(.,'費用')]/text()") == []:
            deliver_fee = 0
        else:
            deliver_fee = diner_div.xpath(
                ".//span[contains(.,'費用')]/text()")[0]
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
            'triggered_at': triggered_at
        }
        return diner

    def combine_uuid_diners_info(self, diners_info, dict_response):
        for diner in diners_info:
            diner['uuid'] = dict_response[diner['title']]
        return diners_info

    def main(self, target, db, html_collection, responses_collection,
             info_collection):
        selector, dict_response, error_log, triggered_at = self.send_location_to_UE(
            target,
            html_collection=html_collection,
            responses_collection=responses_collection)
        if (type(selector) != bool) and dict_response:
            diner_divs = self.get_diner_divs(selector)
            diners_info = [self.get_diner_info(i, triggered_at) for i in diner_divs]
            diners_info = self.combine_uuid_diners_info(
                diners_info, dict_response)
            records = [UpdateOne(
                {'uuid': record['uuid'], 'triggered_at': record['triggered_at']},
                {'$setOnInsert': record},
                upsert=True
            ) for record in diners_info]
            db[info_collection].bulk_write(records)
        else:
            print(error_log['error'])
        self.chrome_close(self.driver)


def lambda_handler(*args, **kwargs):
    start = time.time()
    list_crawler = UEDinerListCrawler()
    list_crawler.main(target, db=db, html_collection='ue_html', responses_collection='ue_responses', info_collection='ue_list')
    stop = time.time()
    pprint.pprint(stop - start)
    time.sleep(5)

    return 'ue_list_test_worked?'
