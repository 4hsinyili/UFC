#  for db control
from pymongo import MongoClient, UpdateOne, InsertOne

# for crawling from js-website
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

# for crawling from API
import requests

# for html parsing
from lxml import etree

# for file handling
import os
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

targets = [
    {
        'title': 'Appworks School',
        'address': '110台北市信義區基隆路一段178號',
        'gps': (25.0424488, 121.562731)
    }, {
        'title': '宏大弘資源回收場',
        'address': '105台北市松山區撫遠街409號',
        'gps': (25.0657733, 121.5649126)
    }, {
        'title': '永清工程行',
        'address': '115南港區成福路121巷30號',
        'gps': (25.0424398, 121.5858762)
    }, {
        'title': '7-ELEVEN 惠安門市',
        'address': '110台北市信義區吳興街520號',
        'gps': (25.0221574, 121.5666836)
    }, {
        'title': '路易莎咖啡',
        'address': '106台北市大安區忠孝東路三段217巷4弄2號',
        'gps': (25.0424876, 121.5400285)
    }
]

db = admin_client['ufc_temp']
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
            if request.url == 'https://www.ubereats.com/api/getFeedV1?localeCode=tw':
                data = json.loads(
                    request.response.body)['data']
                try:
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
            print(len(diner_divs))
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

    def save_triggered_at(self, target, triggered_at, records_count):
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'records_count': records_count,
            'triggered_by': 'get_ue_list',
            'target': target
            })

    def main(self, target, db, info_collection):
        start = time.time()
        selector, dict_response, error_log, triggered_at = self.send_location_to_UE(
            target)
        if (type(selector) != bool) and dict_response:
            diner_divs = self.get_diner_divs(selector)
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
            pprint.pprint('Error Logs:')
            pprint.pprint(error_log)
        stop = time.time()
        self.save_triggered_at(target, triggered_at, len(diners_info))
        print('Get diner list near ', target['title'], ' took ', stop - start, ' seconds.')
        self.chrome_close(self.driver)
        return len(diners_info)


class UEDinerDispatcher():
    def __init__(self, db, info_collection, offset=False, limit=False):
        self.db = db
        self.collection = info_collection
        self.triggered_at = self.get_triggered_at()
        self.diners_info = self.get_diners_info(info_collection, offset, limit)

    def get_triggered_at(self, collection='trigger_log'):
        pipeline = [
            {
                '$match': {'triggered_by': 'get_ue_list'}
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
        temp_collection = 'ue_list_temp'
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


class UEDinerDetailCrawler():
    def __init__(self, info_collection, offset=False, limit=False):
        self.triggered_at = self.get_triggered_at()
        self.diners_info = self.get_diners_info(info_collection, offset, limit)

    def get_triggered_at(self, collection='trigger_log'):
        pipeline = [
            {
                '$match': {'triggered_by': 'get_ue_list'}
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

    def get_diner_detail_from_UE_API(self, diner):
        now = datetime.utcnow()
        if now.hour+8 < 24:
            timestamp = now.replace(hour=(now.hour+8)).timestamp()
        else:
            timestamp = now.replace(day=(now.day+1), hour=(now.hour+8)).timestamp()
        error_log = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            'origin': 'https://www.ubereats.com',
            'x-csrf-token': 'x',
            'authority': 'www.ubereats.com',
            'accept': '*/*',
            'citySlug': "taipei",
            'content-type': 'application/json',
            'cookie': f'''uev2.id.xp=78999d6e-5782-46e9-8ec9-51c900995591; dId=3f972b64-72b1-4786-a1b8-eb6d9ff757bd; uev2.id.session=68755d7c-dfc2-4e16-85b3-6011bb87ddb3; uev2.ts.session=1621306919673; uev2.loc=%7B%22address%22%3A%7B%22\
                address1%22%3A%22AppWorks%20School%22%2C%22address2%22%3A%22%E5%9F%BA%E9%9A%86%E8%B7%AF%E4%B8%80%E6%AE%B5178%E8%99%9F%2C%20%E5%8F%B0%E5%8C%97%E5%B8%82%E4%BF%A1%E7%BE%A9%E5%8D%80%22%2C%22aptOrSuite%22%3A%22%22%2C%22eaterFormattedAddress%22%3A%22110%E5%8F%B0%E7%81%A3%E5%8F%B0%E5%8C%97%E5%B8%82%E4%BF%A1%E7%BE%A9%E5%8D%80%E5%9F%BA%E9%9A%86%E8%B7%AF%E4%B8%80%E6%AE%B5178%E8%99%9F%22%2C%22\
                    subtitle%22%3A%22%E5%9F%BA%E9%9A%86%E8%B7%AF%E4%B8%80%E6%AE%B5178%E8%99%9F%2C%20%E5%8F%B0%E5%8C%97%E5%B8%82%E4%BF%A1%E7%BE%A9%E5%8D%80%22%2C%22title%22%3A%22AppWorks%20School%22%2C%22uuid%22%3A%22%22%7D%2C%22latitude%22%3A25.042416%2C%22longitude%22%3A121.56506%2C%22reference%22%3A%22ChIJg0OvDk-rQjQRGMdB-Cq3egk%22%2C%22\
                        referenceType%22%3A%22google_places%22%2C%22type%22%3A%22google_places%22%2C%22source%22%3A%22rev_geo_reference%22%2C%22address\
                            Components%22%3A%7B%22countryCode%22%3A%22TW%22%2C%22firstLevelSubdivisionCode%22%3A%22%E5%8F%B0%E5%8C%97%E5%B8%82%22%2C%22city%22%3A%22%E4%BF%A1%E7%BE%A9%E5%8D%80%22%2C%22postalCode%22%3A%22110%22%7D%2C%22originType\
                                %22%3A%22user_autocomplete%22%7D; \
                            marketing_vistor_id=e7bb83ce-2281-4977-84f9-49dfc81b2362; jwt-session=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE2MjEzMDY5MjAsImV4cCI6MTYyMTM5MzMyMH0.CHH25X2_6qekvumwvZJOahyJcMK6SGolb8YbPTJuD74; \
                                uev2.gg=true; utm_medium=undefined;utag_main=v_id:01797d6c5f5800037ed1404bc5cc0207801a307000bd0$_sn:1$_se:4$_ss:0$_st:{timestamp}$ses_id:1621306924897%3Bexp-session$_pn:2%3Bexp-session; _userUuid=undefined'''
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
        diner, error_log = self.clean_UE_API_response(UE_API_response, diner)
        time.sleep(1)
        return diner, error_log

    def get_diners_details(self, diners_cursor, data_range=0):
        if data_range == 0:
            diners_info = list(diners_cursor)
        else:
            diners_info = []
            for _ in range(data_range):
                diners_info.append(next(diners_cursor))
        now = datetime.utcnow()
        diners = []
        error_logs = []
        loop_count = 0
        print('Start crawling ', len(diners_info), 'diners at ', now, '.')
        for diner in diners_info:
            diner, error_log = self.get_diner_detail_from_UE_API(diner)
            if diner:
                diners.append(diner)
            if error_log != {}:
                error_logs.append(error_log)
            loop_count += 1
            if loop_count % 500 == 0:
                time.sleep(random.randint(10, 30))
        print('There are ', len(diners_info), ' diners able to send to Appworks School.')
        return diners, error_logs

    def clean_UE_API_response(self, UE_API_response, diner):
        error_log = {}
        try:
            in_range, diner = self.get_in_range(UE_API_response, diner)
            if in_range:
                pass
            else:
                return False, error_log
        except Exception:
            return False, error_log
        try:
            diner = self.get_diner_menu(UE_API_response, diner)
        except Exception:
            error_log = {'error': 'get menu wrong', 'diner': diner['uuid']}
            return False, error_log
        try:
            diner = self.get_open_hours(UE_API_response, diner)
        except Exception:
            error_log = {
                'error': 'get open hours wrong',
                'diner': diner['uuid']
            }
            return False, error_log
        try:
            diner = self.get_other_info(UE_API_response, diner)
        except Exception:
            error_log = {
                'error': 'get other info wrong',
                'diner': diner['uuid']
            }
            return False, error_log
        return diner, error_log

    def get_in_range(self, UE_API_response, diner):
        try:
            in_range = UE_API_response['closedMessage']
            if ('Too far to deliver' in in_range) or ('距離太遠，無法外送' in in_range):
                return False, diner
            else:
                return True, diner
        except Exception:
            return False, diner

    def get_other_info(self, UE_API_response, diner):
        try:
            raw_deliver_time = UE_API_response['etaRange']['text']
            diner['deliver_time'] = int(raw_deliver_time.split('到')[0].replace(' ', ''))
        except Exception:
            diner['deliver_time'] = 0
        try:
            diner['deliver_fee'] = int(UE_API_response['fareBadge']['text'].split('TWD')[0])
        except Exception:
            diner['deliver_fee'] = 0
        diner['budget'] = len(UE_API_response['priceBucket'])
        try:
            diner['rating'] = UE_API_response['rating']['ratingValue']
            diner['view_count'] = int(UE_API_response['rating']['reviewCount'].replace('+', ''))
        except Exception:
            diner['rating'] = 0
            diner['view_count'] = 0
        diner['image'] = UE_API_response['heroImageUrls'][-2]['url']
        diner['tags'] = UE_API_response['cuisineList']
        location_infos = UE_API_response['location']
        diner['address'] = location_infos['streetAddress']
        diner['gps'] = (location_infos['latitude'], location_infos['longitude'])
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
                        item_description = items_map[section_uuid][item_uuid][
                            'description']
                        item_description = item_description.replace('\\n', '')
                    else:
                        item_description = ''
                    item_price = items_map[section_uuid][item_uuid][
                        'price'] // 100
                    item_title = items_map[section_uuid][item_uuid]['title']
                    item_image_url = items_map[section_uuid][item_uuid][
                        'imageUrl']
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
        open_days = set()
        day_map = {
            '星期一': 1,
            '周一': 1,
            '週一': 1,
            '星期二': 2,
            '周二': 2,
            '週二': 2,
            '星期三': 3,
            '周三': 3,
            '週三': 3,
            '星期四': 4,
            '周四': 4,
            '週四': 4,
            '星期五': 5,
            '周五': 5,
            '週五': 5,
            '星期六': 6,
            '周六': 6,
            '週六': 6,
            '星期日': 7,
            '周日': 7,
            '週日': 7,
        }
        days = [1, 2, 3, 4, 5, 6, 7]
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
                start_day = 1
                stop_day = 7
            else:
                start_day = day_range
                start_day = day_map[start_day]
            start_day_index = days.index(start_day)
            if stop_day:
                stop_day_index = days.index(stop_day)
                if start_day_index > stop_day_index:
                    run_days = days[start_day_index:] + days[:stop_day_index]
                else:
                    run_days = days[start_day_index:stop_day_index + 1]
            else:
                run_days = [start_day]
            for sectionHour in hours['sectionHours']:
                start_minute = int(((sectionHour['startTime'] / 60) % 1) * 60)
                start_hour = sectionHour['startTime'] // 60
                stop_minute = int(
                    round(((sectionHour['endTime'] / 60) % 1) * 60, 0))
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
                    open_hour = (run_day, f'{start_hour}:{start_minute}',
                                 f'{stop_hour}:{stop_minute}')
                    open_hours.append(open_hour)
                    open_days.add(run_day)
        diner['open_hours'] = open_hours
        diner['open_days'] = list(open_days)
        return diner

    def save_triggered_at(self, triggered_at, records_count):
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'records_count': records_count,
            'triggered_by': 'get_ue_detail'
            })

    def main(self, db, collection, data_range=0):
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


class UEChecker():
    def __init__(self, db, collection, triggered_by):
        self.db = db
        self.collection = collection
        self.triggered_by = triggered_by
        self.triggered_at = self.get_triggered_at()

    def get_triggered_at(self, collection='trigger_log'):
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
        triggered_at = self.triggered_at
        pipeline = [
            {'$match': {
                'title': {"$exists": False},
                'triggered_at': triggered_at
                }}
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
    running = {'list': False, 'detail': False, 'check': True}
    data_ranges = {'list': 0, 'detail': 0, 'check': 10}
    check_collection = 'ue_detail'
    check_triggered_by = 'get_' + check_collection

    if running['list']:
        list_crawler = UEDinerListCrawler(driver_path=driver_path, headless=True, auto_close=True, inspect=False)
        diners_count_op = list_crawler.main(targets[0], db=db, info_collection='ue_list')
        print('This time crawled ', diners_count_op, ' diners.')
        time.sleep(5)
        dispatcher = UEDinerDispatcher(db, 'ue_list')
        diners_count_ip = dispatcher.main()
        print('There are ', diners_count_ip, ' were latest triggered on ue_list.')
        print("Is dispatcher's input length >= list_crawler's output: ")
        print(diners_count_ip >= diners_count_op)

    if running['detail']:
        start = time.time()
        data_range = data_ranges['detail']
        detail_crawler = UEDinerDetailCrawler('ue_list_temp', offset=False, limit=False)
        diners, error_logs = detail_crawler.main(db=db, collection='ue_detail', data_range=data_range)
        stop = time.time()
        pprint.pprint(stop - start)

    if running['check']:
        data_range = data_ranges['check']
        checker = UEChecker(db, check_collection, check_triggered_by)
        last_records = checker.get_last_records(data_range)
        last_records_count = checker.get_last_records_count()
        errorlogs = checker.get_last_errorlogs()
        checker.check_records(last_records, ['title', 'deliver_time', 'triggered_at'], data_range)
        pprint.pprint(list(errorlogs))
        print(last_records_count)
