# for db control
from pymongo import MongoClient, ASCENDING

# home-made modules
# for file handling
import env
import conf

MONGO_EC2_URI = env.MONGO_EC2_URI
DB_NAME = conf.DB_NAME
admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client[DB_NAME]

if __name__ == '__main__':
    db['ue_list'].create_index([('uuid', ASCENDING), ('triggered_at', ASCENDING)])
    db['fp_list'].create_index([('uuid', ASCENDING), ('triggered_at', ASCENDING)])
    db['ue_detail'].create_index([('uuid', ASCENDING), ('triggered_at', ASCENDING)])
    db['fp_detail'].create_index([('uuid', ASCENDING), ('triggered_at', ASCENDING)])
    db['matched'].create_index([
        ('triggered_at', ASCENDING)
        ])
    db['matched'].create_index([
        ('uuid_ue', ASCENDING),
        ('uuid_fp', ASCENDING)
        ])
    db['matched'].create_index([
        ('triggered_at', ASCENDING),
        ('uuid_ue', ASCENDING),
        ('uuid_fp', ASCENDING)
        ])
    db['trigger_log'].create_index([
        ('triggered_by', ASCENDING),
        ('triggered_at', ASCENDING)
    ])

    print('success')
