from pymongo import MongoClient, ASCENDING
import env

MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc_temp']

if __name__ == '__main__':
    db['ue_list'].create_index([('triggered_at', ASCENDING), ('uuid', ASCENDING)])
    db['fp_list'].create_index([('triggered_at', ASCENDING), ('uuid', ASCENDING)])
    db['ue_detail'].create_index([('triggered_at', ASCENDING), ('uuid', ASCENDING)])
    db['fp_detail'].create_index([('triggered_at', ASCENDING), ('uuid', ASCENDING)])
    db['gm_detail'].create_index([('triggered_at', ASCENDING), ('link', ASCENDING)])

    print('success')
