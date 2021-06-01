#  for db control
from pymongo import InsertOne


class FPDinerDispatcher():
    def __init__(self, db, info_collection, offset=False, limit=False):
        self.db = db
        self.collection = info_collection
        self.triggered_at = self.get_triggered_at()
        self.diners_info = self.get_diners_info(info_collection, offset, limit)

    def get_triggered_at(self, collection='trigger_log'):
        db = self.db
        pipeline = [
            {
                '$match': {'triggered_by': 'get_fp_list'}
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
        db = self.db
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
        db = self.db
        temp_collection = 'fp_list_temp'
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
