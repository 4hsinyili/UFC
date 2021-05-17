import UE_crawl
import env
from pymongo import MongoClient
import time
import json

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

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
driver_path = env.driver_path

ue_list_crawler = UE_crawl.UEDinerListCrawler(driver_path=driver_path, headless=False, auto_close=False, inspect=True)
ue_list_crawler.main(target, db=db, html_collection='html', responses_collection='response', info_collection='ue_temp')


def get_diners_response(driver):
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
                    response = get_diner_response(diners)
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
