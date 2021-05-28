#  for db control
from pymongo import MongoClient, UpdateOne

# for crawling from API
import requests

# for file handling
import json
import env

# for timing and not to get caught
import time
from datetime import datetime
import random

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

db = admin_client['ufc_temp']


class UEDinerDetailCrawler():
    def __init__(self, info_collection, offset=False, limit=False):
        self.diners_info = self.get_diners_info(info_collection, offset, limit)

    def get_triggered_at(self, collection):
        pipeline = [
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
        triggered_at = self.get_triggered_at(info_collection)
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
        timestamp = now.replace(hour=(now.hour+8)).timestamp()
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

    def main(self, db, collection, data_range=0):
        start = time.time()
        diners_cursor = self.diners_info
        diners, error_logs = self.get_diners_details(diners_cursor, data_range=data_range)
        triggered_at = self.get_triggered_at('ue_list')
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
        return diners, error_logs
