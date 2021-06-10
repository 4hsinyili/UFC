#  for db control
from pymongo import UpdateOne

# for crawling from js-website
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

# for html parsing
from lxml import etree

# for file handling
import os
import json
import env

# for timing and not to get caught
import time
from datetime import datetime

# for preview
import pprint

driver_path = env.driver_path


class UEDinerListCrawler():
    def __init__(self, driver_path='lambda', headless=False, auto_close=False, inspect=False):
        self.driver = self.chrome_create(driver_path, headless, auto_close,
                                         inspect)

    def chrome_create(self,
                      driver_path,
                      headless,
                      auto_close,
                      inspect):
        if driver_path != 'lambda':
            chrome_options = webdriver.ChromeOptions()
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
        else:
            options = webdriver.ChromeOptions()
            lambda_options = [
                    '--autoplay-policy=user-gesture-required',
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-breakpad',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-update',
                    '--disable-default-apps',
                    '--disable-dev-shm-usage',
                    '--disable-domain-reliability',
                    '--disable-extensions',
                    '--disable-features=AudioServiceOutOfProcess',
                    '--disable-hang-monitor',
                    '--disable-ipc-flooding-protection',
                    '--disable-notifications',
                    '--disable-offer-store-unmasked-wallet-cards',
                    '--disable-popup-blocking',
                    '--disable-print-preview',
                    '--disable-prompt-on-repost',
                    '--disable-renderer-backgrounding',
                    '--disable-setuid-sandbox',
                    '--disable-speech-api',
                    '--disable-sync',
                    '--disk-cache-size=33554432',
                    '--hide-scrollbars',
                    '--ignore-gpu-blacklist',
                    '--ignore-certificate-errors',
                    '--metrics-recording-only',
                    '--mute-audio',
                    '--no-default-browser-check',
                    '--no-first-run',
                    '--no-pings',
                    '--no-sandbox',
                    '--no-zygote',
                    '--password-store=basic',
                    '--use-gl=swiftshader',
                    '--use-mock-keychain',
                    '--single-process',
                    '--headless']

            # chrome_options.add_argument('--disable-gpu')
            for argument in lambda_options:
                options.add_argument(argument)

            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
            options.add_argument(f'user-agent={user_agent}')
            options.binary_location = os.getcwd() + "/bin/headless-chromium"
            driver = webdriver.Chrome(
                executable_path=os.getcwd() + "/bin/chromedriver",
                chrome_options=options,
                seleniumwire_options={
                    'request_storage_base_dir': '/tmp'
                }
            )
            driver.implicitly_wait(8)
            return driver

    def chrome_close(self, driver):
        driver.close()

    def send_location_to_UE(self, target):
        now = datetime.utcnow()
        triggered_at = datetime.combine(now.date(), datetime.min.time())
        triggered_at = triggered_at.replace(hour=now.hour)
        print('Start getting diners list of ', target['title'], 'begin at', triggered_at, '.')
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
            return False, False, error_log, triggered_at
        time.sleep(10)
        try:
            try:
                driver.find_element_by_xpath('//button[.="Find Food"]').click()
                lang = 'en'
            except Exception:
                driver.find_element_by_xpath('//button[.="尋找食物"]').click()
                lang = 'zh'
        except Exception:
            error_log = {'error': 'send location wrong'}
            return False, False, error_log, triggered_at
        time.sleep(10)
        if lang == 'en':
            locator_xpath = '//button[text() = "Show more"]'
            locator = (By.XPATH, '//button[text() = "Show more"]')
        elif lang == 'zh':
            locator_xpath = '//button[text() = "顯示更多餐廳"]'
            locator = (By.XPATH, '//button[text() = "顯示更多餐廳"]')
        try:
            while len(driver.find_elements_by_xpath(locator_xpath)) > 0:
                try:
                    WebDriverWait(driver, 40, 0.5).until(
                        EC.presence_of_element_located(locator))
                    driver.find_element_by_xpath(locator_xpath).send_keys(
                        Keys.ENTER)
                    WebDriverWait(driver, 40, 0.5).until(
                        EC.presence_of_element_located(locator))
                except Exception:
                    break
        except Exception:
            error_log = {'error': 'scroll wrong'}
            return False, False, error_log, triggered_at
        time.sleep(20)
        html = driver.page_source
        selector = etree.HTML(html)
        dict_response, error_log = self.get_diners_response(driver)
        stop = time.time()
        print('Scroll took: ', stop - start)
        return selector, dict_response, error_log, triggered_at

    def get_diners_response(self,
                            driver=None):
        if not driver:
            driver = self.driver
        error_log = {}
        responses = []
        for request in driver.requests:
            try:
                if request.url == 'https://www.ubereats.com/api/getFeedV1?localeCode=tw':
                    data = json.loads(
                        request.response.body)['data']
                    response = self.get_response_content(data)
                    if response:
                        responses.extend(response)
            except Exception:
                error_log = {'error': 'parse selenium response wrong'}
                return False, error_log
        responses = list(set(responses))
        dict_response = {i[0]: i[1] for i in responses}
        return dict_response, error_log

    def get_response_content(self, data):
        feed_items = data['feedItems']
        contents = []
        if feed_items == []:
            return False
        check_storemap = False
        for feed_item in feed_items:
            if feed_item['type'] == 'STORE':
                check_storemap = True
            elif feed_item['type'] == 'REGULAR_STORE':
                uuid = feed_item['uuid']
                title = feed_item['store']['title']['text']
                content = (title, uuid)
                contents.append(content)
        if check_storemap:
            stores_map = data['storesMap']
            for uuid in stores_map:
                title = stores_map[uuid]['title']
                content = (title, uuid)
                contents.append(content)
        return contents

    def get_diner_divs(self, selector):
        try:
            diner_divs = selector.xpath('''
                //main[@id="main-content"]/div[position()=last()]/div[position()=last()]/div[position()=last()]\
                /div[position()=last()]/div[position()=last()]/div
                ''')
            diner_divs[0].xpath('.//a')[0].get('href')
            str(diner_divs[0].xpath('.//h3/text()')[0])
        except Exception:
            diner_divs = selector.xpath('''
                //main[@id="main-content"]/div[position()=last()]/div[position()=last()]/div[position()=last()]\
                /div[position()=last()]/div[position()=last()-1]/div
                ''')
            diner_divs[0].xpath('.//a')[0].get('href')
            str(diner_divs[0].xpath('.//h3/text()')[0])
        print('There are ', len(diner_divs), ' diners on this target.')
        return diner_divs

    def get_diner_info(self, diner_div, triggered_at):
        try:
            link = diner_div.xpath('.//a')[0].get('href')
            link = 'https://www.ubereats.com' + link
            title = str(diner_div.xpath('.//h3/text()')[0])
        except Exception:
            try:
                link = diner_div.xpath('.//a')[0].get('href')
                link = 'https://www.ubereats.com' + link
                print('There are something wrong about this diner:')
                print(link)
            except Exception:
                print('There are something wrong about a diner in list.')
            return False
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
            try:
                diner['uuid'] = dict_response[diner['title']]
            except Exception:
                diner['uuid'] = False
        return diners_info

    def save_triggered_at(self, target, db, triggered_at, records_count, batch_id):
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'records_count': records_count,
            'triggered_by': 'get_ue_list',
            'batch_id': batch_id,
            'target': target,
            })

    def save_start_at(self, target, db):
        now = datetime.utcnow()
        batch_id = now.timestamp()
        triggered_at = datetime.combine(now.date(), datetime.min.time())
        triggered_at = triggered_at.replace(hour=now.hour)
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'triggered_by': 'get_ue_list_start',
            'batch_id': batch_id,
            'target': target
            })
        return batch_id

    def main(self, target, db, info_collection):
        batch_id = self.save_start_at(target, db)
        start = time.time()
        selector, dict_response, error_log, triggered_at = self.send_location_to_UE(
            target)
        if (type(selector) != bool) and dict_response:
            try:
                diner_divs = self.get_diner_divs(selector)
            except Exception:
                return 0
            diners_info = []
            for diner_div in diner_divs:
                diner_info = self.get_diner_info(diner_div, triggered_at)
                if diner_info:
                    diners_info.append(diner_info)
            diners_info = self.combine_uuid_diners_info(
                diners_info, dict_response)
            records = []
            for diner_info in diners_info:
                if diner_info['uuid']:
                    record = UpdateOne(
                        {'uuid': diner_info['uuid'], 'triggered_at': diner_info['triggered_at']},
                        {'$setOnInsert': diner_info},
                        upsert=True
                    )
                    records.append(record)
            db[info_collection].bulk_write(records)
            print('There are ', len(records), ' diners successfully paresed.')
        else:
            diners_info = []
            pprint.pprint('Error Logs:')
            pprint.pprint(error_log)
        stop = time.time()
        self.save_triggered_at(target, db, triggered_at, len(diners_info), batch_id)
        print('Get diner list near ', target['title'], ' took ', stop - start, ' seconds.')
        self.chrome_close(self.driver)
        return len(diners_info)
