import configparser
import os

file_path = '.conf'

CONFIG = configparser.ConfigParser()
if os.getcwd() == '/var/task':
    file_path = 'src/' + file_path
print(os.getcwd())
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

GET_UE_LIST = CONFIG['TriggeredBy']['get_ue_list']
GET_FP_LIST = CONFIG['TriggeredBy']['get_fp_list']
GET_UE_DETAIL = CONFIG['TriggeredBy']['get_ue_detail']
GET_FP_DETAIL = CONFIG['TriggeredBy']['get_fp_detail']
MATCH = CONFIG['TriggeredBy']['match']
PLACE = CONFIG['TriggeredBy']['place']
