import pprint
import env
from pymongo import MongoClient
# import time
import datetime

MONGO_EC2_URI = env.MONGO_EC2_URI
admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client['ufc']


class TriggerLog():
    def __init__(self, db):
        self.db = db

    def get_log(self, end_time, start_time):
        cursor = db.trigger_log.find({
            "triggered_at": {
                "$gte": start_time,
                "$lte": end_time
                }
        })
        data = []
        for record in cursor:
            del record['_id']
            record['triggered_at'] = record['triggered_at'].strftime('%Y-%m-%d %H:%M:%S')
            data.append(record)
        cursor.close()
        return data

    def parse_data(self, data, trigered_by):
        result = []
        for record in data:
            if (record['triggered_by'] == trigered_by) and (trigered_by == 'get_ue_list'):
                del record['target']
                result.append(record)
            elif record['triggered_by'] == trigered_by:
                result.append(record)
        return result

    def main(self, end_time, start_time):
        data = self.get_log(end_time, start_time)
        ue_list_data = self.parse_data(data, 'get_ue_list')
        fp_list_data = self.parse_data(data, 'get_fp_list')
        ue_detail_data = self.parse_data(data, 'get_ue_detail')
        fp_detail_data = self.parse_data(data, 'get_fp_detail')
        match_data = self.parse_data(data, 'match')
        place_data = self.parse_data(data, 'place')

        return {
            'get_ue_list': ue_list_data,
            'get_fp_list': fp_list_data,
            'get_ue_detail': ue_detail_data,
            'get_fp_detail': fp_detail_data,
            'match': match_data,
            'place': place_data,
        }


if __name__ == '__main__':
    end_time = datetime.datetime.combine(datetime.datetime.today().date(), datetime.time.max)
    start_time = datetime.datetime.combine(
        datetime.datetime.today().date(),
        datetime.time.min)
    trigger_log = TriggerLog(db)
    data = trigger_log.main(end_time, start_time)
    pprint.pprint(data)
