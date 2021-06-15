import pprint
import env
from pymongo import MongoClient
# import time
from collections import defaultdict
import datetime

MONGO_EC2_URI = env.MONGO_EC2_URI
admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client['ufc']


class TriggerLog():
    def __init__(self, db):
        self.db = db

    def get_log(self, end_time, start_time):
        cursor = db.trigger_log.aggregate(
            [
                {
                   "$match": {
                        "triggered_at": {
                           "$gte": start_time,
                           "$lte": end_time
                            },
                        "batch_id": {"$exists": True}
                        },
                },
                {
                    "$group": {
                        "_id": {
                            "batch_id": "$batch_id",
                            "triggered_by": "$triggered_by"
                        },
                        "data": {
                            "$push": "$$ROOT"
                        }
                    }
                }
            ]
        )
        data = []
        for record in cursor:
            key = {"triggered_by": record['_id']['triggered_by'], "batch_id": record['_id']['batch_id']}
            result = (key, record['data'])
            data.append(result)
        cursor.close()
        # pprint.pprint(data)
        return data

    def parse_data(self, data, trigered_by):
        result = defaultdict(dict)
        for bucket in data:
            key = bucket[0]
            if key['triggered_by'] == trigered_by:
                bucket_val = bucket[1]
                for val in bucket_val:
                    val['log_time'] = val['_id'].generation_time
                    val['log_time'] = val['log_time'].strftime('%Y-%m-%d %H:%M:%S')
                    del val['_id']
                    val['triggered_at'] = val['triggered_at'].strftime('%Y-%m-%d %H:%M:%S')
                result[key['triggered_by']][key['batch_id']] = bucket_val
        if result == []:
            return False
        return result

    def main(self, end_time, start_time):
        data = self.get_log(end_time, start_time)
        ue_list_start_data = self.parse_data(data, 'get_ue_list_start')
        fp_list_start_data = self.parse_data(data, 'get_fp_list_start')
        ue_list_data = self.parse_data(data, 'get_ue_list')
        fp_list_data = self.parse_data(data, 'get_fp_list')
        ue_detail_data = self.parse_data(data, 'get_ue_detail')
        fp_detail_data = self.parse_data(data, 'get_fp_detail')
        match_start_data = self.parse_data(data, 'match_start')
        place_start_data = self.parse_data(data, 'place_start')
        match_data = self.parse_data(data, 'match')
        place_data = self.parse_data(data, 'place')
        result = {}
        result.update(ue_list_start_data)
        result.update(fp_list_start_data)
        result.update(ue_list_data)
        result.update(fp_list_data)
        result.update(ue_detail_data)
        result.update(fp_detail_data)
        result.update(match_start_data)
        result.update(place_start_data)
        result.update(match_data)
        result.update(place_data)

        # return data
        return result


if __name__ == '__main__':
    end_time = datetime.datetime.combine(datetime.datetime.today().date(), datetime.time.max)
    start_time = datetime.datetime.combine(
        datetime.datetime.today().date(),
        datetime.time.min)
    trigger_log = TriggerLog(db)
    data = trigger_log.main(end_time, start_time)
    pprint.pprint(data)
