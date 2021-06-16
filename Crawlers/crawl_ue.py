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

MONGO_EC2_URI = env.MONGO_EC2_URI
admin_client = MongoClient(MONGO_EC2_URI)

targets = [{
    'title': 'Appworks School',
    'address': '110台北市信義區基隆路一段178號',
    'gps': (25.0424488, 121.562731),
    'batch_id': 0.0001
}, {
    'title': '宏大弘資源回收場',
    'address': '105台北市松山區撫遠街409號',
    'gps': (25.0657733, 121.5649126),
    'batch_id': 0.0001
}, {
    'title': '永清工程行',
    'address': '115南港區成福路121巷30號',
    'gps': (25.0424398, 121.5858762),
    'batch_id': 0.0001
}, {
    'title': '7-ELEVEN 惠安門市',
    'address': '110台北市信義區吳興街520號',
    'gps': (25.0221574, 121.5666836),
    'batch_id': 0.0001
}, {
    'title': '路易莎咖啡',
    'address': '106台北市大安區忠孝東路三段217巷4弄2-5號',
    'gps': (25.0424876, 121.5400285),
    'batch_id': 0.0001
}]

db = admin_client['ufc']
driver_path = env.DRIVER_PATH


class UEDinerListCrawler():
    def __init__(self,
                 target,
                 db,
                 write_collection,
                 log_collection,
                 driver_path='lambda',
                 headless=False,
                 auto_close=False,
                 inspect=False):
        self.target = target
        self.batch_id = target['batch_id']
        self.db = db
        self.write_collection = write_collection
        self.log_collection = log_collection
        self.driver = self.chrome_create(driver_path, headless, auto_close,
                                         inspect)
        self.triggered_at = self.generate_triggered_at()

    def chrome_create(self, driver_path, headless, auto_close, inspect):
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
                '--disable-component-update', '--disable-default-apps',
                '--disable-dev-shm-usage', '--disable-domain-reliability',
                '--disable-extensions',
                '--disable-features=AudioServiceOutOfProcess',
                '--disable-hang-monitor', '--disable-ipc-flooding-protection',
                '--disable-notifications',
                '--disable-offer-store-unmasked-wallet-cards',
                '--disable-popup-blocking', '--disable-print-preview',
                '--disable-prompt-on-repost',
                '--disable-renderer-backgrounding', '--disable-setuid-sandbox',
                '--disable-speech-api', '--disable-sync',
                '--disk-cache-size=33554432', '--hide-scrollbars',
                '--ignore-gpu-blacklist', '--ignore-certificate-errors',
                '--metrics-recording-only', '--mute-audio',
                '--no-default-browser-check', '--no-first-run', '--no-pings',
                '--no-sandbox', '--no-zygote', '--password-store=basic',
                '--use-gl=swiftshader', '--use-mock-keychain',
                '--single-process', '--headless'
            ]

            # chrome_options.add_argument('--disable-gpu')
            for argument in lambda_options:
                options.add_argument(argument)

            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
            options.add_argument(f'user-agent={user_agent}')
            options.binary_location = os.getcwd() + "/bin/headless-chromium"
            driver = webdriver.Chrome(
                executable_path=os.getcwd() + "/bin/chromedriver",
                chrome_options=options,
                seleniumwire_options={'request_storage_base_dir': '/tmp'})
            driver.implicitly_wait(8)
            return driver

    def chrome_close(self, driver):
        driver.close()

    def generate_triggered_at(self):
        now = datetime.utcnow()
        triggered_at = datetime.combine(now.date(), datetime.min.time())
        triggered_at = triggered_at.replace(hour=now.hour)
        return triggered_at

    def send_location_to_UE(self):
        target = self.target
        triggered_at = self.triggered_at
        print('Start getting diners list of ', target['title'], 'begin at',
              triggered_at, '.')
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
            print('Send location wrong.')
            return False, False, error_log
        time.sleep(10)

        try:
            try:
                driver.find_element_by_xpath('//button[.="Find Food"]').click()
                lang = 'en'
            except Exception:
                driver.find_element_by_xpath('//button[.="尋找食物"]').click()
                lang = 'zh'
        except Exception:
            error_log = {'error': 'click button wrong'}
            print('Click button wrong.')
            return False, False, error_log
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
            print('Scroll wrong.')
            return False, False, error_log
        time.sleep(20)

        html = driver.page_source
        selector = etree.HTML(html)
        dict_response, error_log = self.parse_driver_response()
        stop = time.time()
        print('Scroll took: ', stop - start)
        return selector, dict_response, error_log

    def parse_driver_response(self):
        driver = self.driver
        error_log = {}
        title_uuid_pairs = []

        for request in driver.requests:
            try:
                if request.url == 'https://www.ubereats.com/api/getFeedV1?localeCode=tw':
                    data = json.loads(request.response.body)['data']
                    title_uuid_pairs_pt = self.get_uuid_from_response(data)

                    if title_uuid_pairs_pt:
                        title_uuid_pairs.extend(title_uuid_pairs_pt)
            except Exception:
                error_log = {'error': 'parse selenium response wrong'}
                return False, error_log

        title_uuid_pairs = list(set(title_uuid_pairs))
        title_uuid_dict = {i[0]: i[1] for i in title_uuid_pairs}
        return title_uuid_dict, error_log

    def get_uuid_from_response(self, data):
        feed_items = data['feedItems']
        title_uuid_pairs = []
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
                title_uuid_pairs.append(content)

        if check_storemap:
            stores_map = data['storesMap']
            for uuid in stores_map:
                title = stores_map[uuid]['title']
                content = (title, uuid)
                title_uuid_pairs.append(content)

        return title_uuid_pairs

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

    def get_diner_info(self, diner_div):
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
            choice = 1
        except Exception:
            choice = 0

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
            'choice': choice,
            'triggered_at': self.triggered_at
        }
        return diner

    def give_diners_uuid(self, diners_info, dict_response):
        for diner in diners_info:
            try:
                diner['uuid'] = dict_response[diner['title']]
            except Exception:
                diner['uuid'] = False
        return diners_info

    def save_triggered_at(self, records_count):
        db = self.db
        log_collection = self.log_collection
        db[log_collection].insert_one({
            'triggered_at': self.triggered_at,
            'records_count': records_count,
            'triggered_by': 'get_ue_list',
            'batch_id': self.batch_id,
            'target': self.target,
        })

    def save_start_at(self):
        db = self.db
        log_collection = self.log_collection
        db[log_collection].insert_one({
            'triggered_at': self.triggered_at,
            'triggered_by': 'get_ue_list_start',
            'batch_id': self.batch_id,
            'target': self.target
        })

    def assemble_diners_info(self, diner_divs, title_uuid_dict):
        diners_info = []
        for diner_div in diner_divs:
            diner_info = self.get_diner_info(diner_div)
            if diner_info:
                diners_info.append(diner_info)
        diners_info = self.give_diners_uuid(diners_info, title_uuid_dict)
        return diners_info

    def save_records(self, diners_info):
        db = self.db
        write_collection = self.write_collection
        records = []
        for diner_info in diners_info:
            if diner_info['uuid']:
                record = UpdateOne(
                    {
                        'uuid': diner_info['uuid'],
                        'triggered_at': diner_info['triggered_at']
                    }, {'$setOnInsert': diner_info},
                    upsert=True)
                records.append(record)
        db[write_collection].bulk_write(records)
        return len(records)

    def main(self):
        self.save_start_at()
        start = time.time()
        selector, title_uuid_dict, error_log = self.send_location_to_UE()
        records_count = 0

        if (type(selector) != bool) and title_uuid_dict:
            # if use '''if selector and title_uuid_dict:''' will trigger follow warning:
            # The behavior of this method will change in future versions. Use specific 'len(elem)' or 'elem is not None' test instead.
            try:
                diner_divs = self.get_diner_divs(selector)
            except Exception:
                print('Get diner divs wrong.')
                return records_count

            diners_info = self.assemble_diners_info(diner_divs,
                                                    title_uuid_dict)
            records_count = self.save_records(diners_info)
            print('There are ', records_count, ' diners successfully paresed.')

        else:
            pprint.pprint('Error Logs:')
            pprint.pprint(error_log)

        stop = time.time()
        self.save_triggered_at(records_count)
        print('Get diner list near ', self.target['title'], ' took ',
              stop - start, ' seconds.')
        self.chrome_close(self.driver)
        return records_count


class UEDinerDispatcher():
    def __init__(self,
                 db,
                 read_collection,
                 write_collection,
                 log_collection,
                 triggered_by,
                 offset=False,
                 limit=False):
        self.db = db
        self.read_collection = read_collection
        self.write_collection = write_collection
        self.log_collection = log_collection
        self.triggered_by = triggered_by
        self.triggered_at = self.get_triggered_at()
        self.diners_cursor = self.get_diners_info(offset, limit)

    def get_triggered_at(self):
        db = self.db
        log_collection = self.log_collection
        triggered_by = self.triggered_by
        pipeline = [{
            '$match': {
                'triggered_by': triggered_by
            }
        }, {
            '$sort': {
                'triggered_at': 1
            }
        }, {
            '$group': {
                '_id': None,
                'triggered_at': {
                    '$last': '$triggered_at'
                }
            }
        }]
        cursor = db[log_collection].aggregate(pipeline=pipeline)
        result = next(cursor)['triggered_at']
        cursor.close()
        return result

    def get_diners_info(self, offset=0, limit=0):
        db = self.db
        triggered_at = self.triggered_at
        read_collection = self.read_collection
        pipeline = [{
            '$match': {
                'title': {
                    "$exists": True
                },
                'triggered_at': triggered_at
            }
        }, {
            '$sort': {
                'uuid': 1
            }
        }]
        if offset > 0:
            pipeline.append({'$skip': offset})
        if limit > 0:
            pipeline.append({'$limit': limit})
        cursor = db[read_collection].aggregate(pipeline=pipeline,
                                               allowDiskUse=True)
        return cursor

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


class UEDinerDetailCrawler():
    def __init__(self,
                 target,
                 headers,
                 ue_detail_url,
                 db,
                 read_collection,
                 write_collection,
                 log_collection,
                 triggered_by,
                 offset=False,
                 limit=False):
        self.target = target
        self.headers = headers
        self.ue_detail_url = ue_detail_url
        self.db = db
        self.read_collection = read_collection
        self.write_collection = write_collection
        self.log_collection = log_collection
        self.triggered_by = triggered_by
        self.triggered_at, self.batch_id = self.get_pre_run_info()
        self.diners_cursor = self.get_diners_cursor(offset,
                                                    limit)
        self.order_time = self.generate_order_time()

    def get_pre_run_info(self):
        db = self.db
        tirggered_by = self.triggered_by
        log_collection = self.log_collection
        pipeline = [{
            '$match': {
                'triggered_by': tirggered_by
            }
        }, {
            '$sort': {
                'triggered_at': 1
            }
        }, {
            '$group': {
                '_id': None,
                'triggered_at': {
                    '$last': '$triggered_at'
                },
                'batch_id': {
                    '$last': '$batch_id'
                }
            }
        }]
        cursor = db[log_collection].aggregate(pipeline=pipeline)
        raw = next(cursor)
        triggered_at = raw['triggered_at']
        batch_id = raw['batch_id']
        cursor.close()
        return triggered_at, batch_id

    def get_diners_cursor(self, offset=0, limit=0):
        db = self.db
        triggered_at = self.triggered_at
        read_collection = self.read_collection
        pipeline = [{
            '$match': {
                'title': {
                    "$exists": True
                },
                'triggered_at': triggered_at
            }
        }, {
            '$sort': {
                'uuid': 1
            }
        }]
        if offset > 0:
            pipeline.append({'$skip': offset})
        if limit > 0:
            pipeline.append({'$limit': limit})
        cursor = db[read_collection].aggregate(pipeline=pipeline,
                                               allowDiskUse=True)
        return cursor

    def generate_order_time(self):
        now = datetime.utcnow()
        if now.hour + 8 < 24:
            order_time = now.replace(hour=(now.hour + 8)).timestamp()
        else:
            order_time = now.replace(day=(now.day + 1),
                                     hour=(now.hour - 16)).timestamp()
        return order_time

    def get_diner_detail_from_api(self, diner):
        order_time = str(self.order_time)
        error_log = {}
        headers = self.headers
        headers['cookie'] = headers['cookie'].replace('{order_time}', order_time)
        deatil_url = self.ue_detail_url

        try:
            payload = {
                'storeUuid': diner['uuid'],
                'sfNuggetCount': 1  # clicked how many stores in this session
            }
        except Exception:
            error_log = {'error': 'parse diner_info wrong', 'diner': diner}
            print('Parse diner_info wrong.')
            return False, error_log

        try:
            deatil_response = requests.post(deatil_url,
                                            headers=headers,
                                            data=json.dumps(payload))
            detail = json.loads(deatil_response.content)['data']
        except Exception:
            error_log = {'error': 'store_api wrong', 'diner': diner}
            return False, error_log

        diner, error_log = self.clean_detail_response(detail, diner)
        time.sleep(1)

        return diner, error_log

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
            if error_log != {}:
                error_logs.append(error_log)
            loop_count += 1
            if loop_count % 500 == 0:
                time.sleep(random.randint(10, 30))
        print('There are ', len(diners_info),
              ' diners able to send to Appworks School.')
        return diners, error_logs

    def clean_detail_response(self, detail, diner):
        error_log = {}
        in_range, diner = self.get_in_range(detail, diner)
        if not in_range:
            return False, error_log

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

    def get_in_range(self, detail, diner):
        try:
            in_range = detail['closedMessage']
            if ('Too far to deliver' in in_range) or ('距離太遠，無法外送' in in_range):
                return False, diner
            else:
                return True, diner
        except Exception:
            return False, diner

    def get_other_info(self, detail, diner):
        try:
            raw_deliver_time = detail['etaRange']['text']
            diner['deliver_time'] = int(
                raw_deliver_time.split('到')[0].replace(' ', ''))
        except Exception:
            diner['deliver_time'] = 0

        try:
            diner['deliver_fee'] = int(
                detail['fareBadge']['text'].split('TWD')[0])
        except Exception:
            diner['deliver_fee'] = 0

        diner['budget'] = len(detail['priceBucket'])

        try:
            diner['rating'] = detail['rating']['ratingValue']
            diner['view_count'] = int(detail['rating']['reviewCount'].replace(
                '+', ''))
        except Exception:
            diner['rating'] = 0
            diner['view_count'] = 0

        diner['image'] = detail['heroImageUrls'][-2]['url']
        diner['tags'] = detail['cuisineList']
        location_info = detail['location']
        diner['address'] = location_info['streetAddress']
        diner['gps'] = (location_info['latitude'], location_info['longitude'])
        return diner

    def get_diner_menu(self, detail, diner):
        menu = []
        sections = detail['sections']
        subsections_map = detail['subsectionsMap']
        items_map = detail['sectionEntitiesMap']
        item_dict = {}
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
        business_hours = detail['hours']
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
                    {
                        'link': diner['link'],
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
            self.save_triggered_at(diners_count)
        return diners, error_logs


class UEChecker():
    def __init__(self, db, read_collection, triggered_by):
        self.db = db
        self.read_collection = read_collection
        self.triggered_by = triggered_by
        self.triggered_at = self.get_triggered_at()

    def get_triggered_at(self, collection='trigger_log'):
        db = self.db
        pipeline = [{
            '$match': {
                'triggered_by': self.triggered_by
            }
        }, {
            '$sort': {
                'triggered_at': 1
            }
        }, {
            '$group': {
                '_id': None,
                'triggered_at': {
                    '$last': '$triggered_at'
                }
            }
        }]
        cursor = db[collection].aggregate(pipeline=pipeline)
        result = next(cursor)['triggered_at']
        cursor.close()
        return result

    def get_latest_records(self, limit=0):
        db = self.db
        read_collection = self.read_collection
        triggered_at = self.triggered_at
        pipeline = [{
            '$match': {
                'title': {
                    "$exists": True
                },
                'triggered_at': triggered_at
            }
        }, {
            '$sort': {
                'uuid': 1
            }
        }]
        if limit > 0:
            pipeline.append({'$limit': limit})
        result = db[read_collection].aggregate(pipeline=pipeline,
                                               allowDiskUse=True)
        return result

    def get_latest_records_count(self):
        db = self.db
        read_collection = self.read_collection
        triggered_at = self.triggered_at
        pipeline = [{
            '$match': {
                'title': {
                    "$exists": True
                },
                'triggered_at': triggered_at
            }
        }, {
            '$count': 'triggered_at'
        }]
        cursor = db[read_collection].aggregate(pipeline=pipeline,
                                               allowDiskUse=True)
        result = next(cursor)['triggered_at']
        return result

    def get_latest_errorlogs(self):
        db = self.db
        read_collection = self.read_collection
        triggered_at = self.get_triggered_at()
        pipeline = [{
            '$match': {
                'title': {
                    "$exists": False
                },
                'triggered_at': triggered_at
            }
        }]
        cursor = db[read_collection].aggregate(pipeline=pipeline,
                                               allowDiskUse=True)
        return cursor

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
    check_collection = 'ue_detail'
    check_triggered_by = 'get_' + check_collection
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'origin':
        'https://www.ubereats.com',
        'x-csrf-token':
        'x',
        'authority':
        'www.ubereats.com',
        'accept':
        '*/*',
        'citySlug':
        "taipei",
        'content-type':
        'application/json',
        'cookie':
        'uev2.id.xp=78999d6e-5782-46e9-8ec9-51c900995591; dId=3f972b64-72b1-4786-a1b8-eb6d9ff757bd; uev2.id.session=68755d7c-dfc2-4e16-85b3-6011bb87ddb3; uev2.ts.session=1621306919673; uev2.loc=%7B%22address%22%3A%7B%22\
                address1%22%3A%22AppWorks%20School%22%2C%22address2%22%3A%22%E5%9F%BA%E9%9A%86%E8%B7%AF%E4%B8%80%E6%AE%B5178%E8%99%9F%2C%20%E5%8F%B0%E5%8C%97%E5%B8%82%E4%BF%A1%E7%BE%A9%E5%8D%80%22%2C%22aptOrSuite%22%3A%22%22%2C%22eaterFormattedAddress%22%3A%22110%E5%8F%B0%E7%81%A3%E5%8F%B0%E5%8C%97%E5%B8%82%E4%BF%A1%E7%BE%A9%E5%8D%80%E5%9F%BA%E9%9A%86%E8%B7%AF%E4%B8%80%E6%AE%B5178%E8%99%9F%22%2C%22\
                    subtitle%22%3A%22%E5%9F%BA%E9%9A%86%E8%B7%AF%E4%B8%80%E6%AE%B5178%E8%99%9F%2C%20%E5%8F%B0%E5%8C%97%E5%B8%82%E4%BF%A1%E7%BE%A9%E5%8D%80%22%2C%22title%22%3A%22AppWorks%20School%22%2C%22uuid%22%3A%22%22%7D%2C%22latitude%22%3A25.042416%2C%22longitude%22%3A121.56506%2C%22reference%22%3A%22ChIJg0OvDk-rQjQRGMdB-Cq3egk%22%2C%22\
                        referenceType%22%3A%22google_places%22%2C%22type%22%3A%22google_places%22%2C%22source%22%3A%22rev_geo_reference%22%2C%22address\
                            Components%22%3A%7B%22countryCode%22%3A%22TW%22%2C%22firstLevelSubdivisionCode%22%3A%22%E5%8F%B0%E5%8C%97%E5%B8%82%22%2C%22city%22%3A%22%E4%BF%A1%E7%BE%A9%E5%8D%80%22%2C%22postalCode%22%3A%22110%22%7D%2C%22originType\
                                %22%3A%22user_autocomplete%22%7D; \
                            marketing_vistor_id=e7bb83ce-2281-4977-84f9-49dfc81b2362; jwt-session=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE2MjEzMDY5MjAsImV4cCI6MTYyMTM5MzMyMH0.CHH25X2_6qekvumwvZJOahyJcMK6SGolb8YbPTJuD74; \
                                uev2.gg=true; utm_medium=undefined;utag_main=v_id:01797d6c5f5800037ed1404bc5cc0207801a307000bd0$_sn:1$_se:4$_ss:0$_st:{order_time}$ses_id:1621306924897%3Bexp-session$_pn:2%3Bexp-session; _userUuid=undefined'
    }
    ue_deatil_url = 'https://www.ubereats.com/api/getStoreV1?localeCode=tw'
    target = targets[0]

    if running['list']:
        data_range = data_ranges['list']
        list_crawler = UEDinerListCrawler(target,
                                          db,
                                          write_collection='ue_list',
                                          log_collection='trigger_log',
                                          driver_path=driver_path,
                                          headless=True,
                                          auto_close=True,
                                          inspect=False)
        diners_count_op = list_crawler.main()
        print('This time crawled ', diners_count_op, ' diners.')
        time.sleep(5)
        dispatcher = UEDinerDispatcher(db,
                                       read_collection='ue_list',
                                       write_collection='ue_list_temp',
                                       log_collection='trigger_log',
                                       triggered_by='get_ue_list',
                                       limit=data_range)
        diners_count_ip = dispatcher.main()
        print('There are ', diners_count_ip,
              ' were latest triggered on ue_list.')
        print("Is dispatcher's input length >= list_crawler's output: ")
        print(diners_count_ip >= diners_count_op)

    if running['detail']:
        start = time.time()
        data_range = data_ranges['detail']
        detail_crawler = UEDinerDetailCrawler(target,
                                              headers,
                                              ue_deatil_url,
                                              db,
                                              read_collection='ue_list',
                                              write_collection='ue_list_temp',
                                              log_collection='trigger_log',
                                              triggered_by='get_ue_list',
                                              limit=data_range)
        diners, error_logs = detail_crawler.main()
        stop = time.time()
        pprint.pprint(stop - start)

    if running['check']:
        data_range = data_ranges['check']
        checker = UEChecker(db, check_collection, check_triggered_by)
        latest_records = checker.get_latest_records(data_range)
        # checker.check_duplicate(latest_records)
        latest_records_count = checker.get_latest_records_count()
        errorlogs = checker.get_latest_errorlogs()
        checker.check_records(latest_records,
                              ['title', 'deliver_time', 'triggered_at'],
                              data_range)
        pprint.pprint(list(errorlogs))
        print(latest_records_count)
