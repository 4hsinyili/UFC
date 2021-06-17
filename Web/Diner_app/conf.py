import configparser
import os

file_path = '.conf'

CONFIG = configparser.ConfigParser()
if os.getcwd().endswith('/Web'):
    file_path = 'Diner_app/' + file_path

CONFIG.read(file_path)

DB_NAME = CONFIG['Local']['db_prod_name']

UE_LIST_COLLECTION = CONFIG['Collections']['ue_list']
UE_LIST_TEMP_COLLECTION = CONFIG['Collections']['ue_list_temp']
UE_DETAIL_COLLECTION = CONFIG['Collections']['ue_detail']

FP_LIST_COLLECTION = CONFIG['Collections']['fp_list']
FP_LIST_TEMP_COLLECTION = CONFIG['Collections']['fp_list_temp']
FP_DETAIL_COLLECTION = CONFIG['Collections']['fp_detail']

MATCHED_COLLECTION = CONFIG['Collections']['matched']
LOG_COLLECTION = CONFIG['Collections']['trigger_log']
STEPFUNCTION_LOG_COLLECTION = CONFIG['Collections']['stepfunction_log']

GET_UE_LIST_START = CONFIG['TriggeredBy']['get_ue_list_start']
GET_FP_LIST_START = CONFIG['TriggeredBy']['get_fp_list_start']
GET_UE_LIST = CONFIG['TriggeredBy']['get_ue_list']
GET_FP_LIST = CONFIG['TriggeredBy']['get_fp_list']
GET_UE_DETAIL = CONFIG['TriggeredBy']['get_ue_detail']
GET_FP_DETAIL = CONFIG['TriggeredBy']['get_fp_detail']
MATCH_START = CONFIG['TriggeredBy']['match_start']
PLACE_START = CONFIG['TriggeredBy']['place_start']
MATCH = CONFIG['TriggeredBy']['match']
PLACE = CONFIG['TriggeredBy']['place']
TRIGGERED_BY_LIST = [
    GET_UE_LIST_START, GET_FP_LIST_START, GET_UE_LIST, GET_FP_LIST,
    GET_UE_DETAIL, GET_FP_DETAIL, MATCH_START, PLACE_START, MATCH, PLACE
]
