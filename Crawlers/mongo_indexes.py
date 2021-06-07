from pymongo import MongoClient, ASCENDING
import env

MONGO_ATLAS_URI = env.MONGO_ATLAS_URI
admin_client = MongoClient(MONGO_ATLAS_URI)
db = admin_client['ufc']

if __name__ == '__main__':
    db['ue_list'].create_index([('triggered_at', ASCENDING), ('uuid', ASCENDING)])
    db['fp_list'].create_index([('triggered_at', ASCENDING), ('uuid', ASCENDING)])
    db['ue_detail'].create_index([('triggered_at', ASCENDING), ('uuid', ASCENDING)])
    db['fp_detail'].create_index([('triggered_at', ASCENDING), ('uuid', ASCENDING)])
    db['gm_detail'].create_index([('triggered_at', ASCENDING), ('link', ASCENDING)])
    db['matched'].create_index([
        ('uuid_ue', ASCENDING),
        ('uuid_fp', ASCENDING),
        ('uuid_matched', ASCENDING),
        ('triggered_at_ue', ASCENDING),
        ('triggered_at_fp', ASCENDING)
        ])
    db['placed'].create_index([
        ('uuid_ue', ASCENDING),
        ('uuid_fp', ASCENDING),
        ('uuid_gm', ASCENDING),
        ('uuid_matched', ASCENDING),
        ('triggered_at_ue', ASCENDING),
        ('triggered_at_fp', ASCENDING),
        ('triggered_at_gm', ASCENDING)
    ])

    print('success')
