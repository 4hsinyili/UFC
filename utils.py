import json
from datetime import datetime
from pymongo import InsertOne
import pprint
import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def read_json(file_path):
    with open(file_path) as json_file:
        json_object = json.load(json_file)
    return json_object


def generate_triggered_at():
    now = datetime.utcnow()
    triggered_at = datetime.combine(now.date(), datetime.min.time())
    triggered_at = triggered_at.replace(hour=now.hour)
    return triggered_at


def get_triggered_at(instance):
    db = instance.db
    log_collection = instance.log_collection
    r_triggered_by = instance.r_triggered_by
    pipeline = [{
        '$match': {
            'triggered_by': r_triggered_by
        }
    }, {
        '$sort': {
            'triggered_at': 1
        }
    }, {
        '$group': {
            '_id': None,
            'triggered_at': {
                '$last': '$triggered_at'
            }
        }
    }]
    cursor = db[log_collection].aggregate(pipeline=pipeline)
    result = next(cursor)['triggered_at']
    cursor.close()
    return result


def get_diners_cursor(instance, offset=0, limit=0):
    db = instance.db
    triggered_at = instance.triggered_at
    read_collection = instance.read_collection
    pipeline = [{
        '$match': {
            'title': {
                "$exists": True
            },
            'triggered_at': triggered_at
        }
    }, {
        '$sort': {
            'uuid': 1
        }
    }]
    if offset > 0:
        pipeline.append({'$skip': offset})
    if limit > 0:
        pipeline.append({'$limit': limit})
    cursor = db[read_collection].aggregate(pipeline=pipeline,
                                           allowDiskUse=True)
    return cursor


def get_pre_run_info(instance):
    db = instance.db
    r_triggered_by = instance.r_triggered_by
    log_collection = instance.log_collection
    pipeline = [{
        '$match': {
            'triggered_by': r_triggered_by
        }
    }, {
        '$sort': {
            'triggered_at': 1
        }
    }, {
        '$group': {
            '_id': None,
            'triggered_at': {
                '$last': '$triggered_at'
            },
            'batch_id': {
                '$last': '$batch_id'
            }
        }
    }]
    cursor = db[log_collection].aggregate(pipeline=pipeline)
    raw = next(cursor)
    triggered_at = raw['triggered_at']
    batch_id = raw['batch_id']
    cursor.close()
    return triggered_at, batch_id


def save_start_at(instance):
    db = instance.db
    triggered_at = instance.triggered_at
    log_collection = instance.log_collection
    w_triggered_by = instance.w_triggered_by
    start_trigger = w_triggered_by + '_start'

    record = {
        'triggered_at': triggered_at,
        'triggered_by': start_trigger,
    }

    if w_triggered_by == 'get_ue_list':
        record['target'] = instance.target
        record['batch_id'] = instance.batch_id
    elif w_triggered_by == 'get_fp_list':
        now = datetime.utcnow()
        batch_id = now.timestamp()
        record['target'] = instance.target
        record['batch_id'] = batch_id
    elif w_triggered_by == 'match':
        now = datetime.utcnow()
        batch_id = now.timestamp()
        record['batch_id'] = batch_id
    elif w_triggered_by == 'place':
        record['batch_id'] = instance.batch_id
    # pprint.pprint(record)
    db[log_collection].insert_one(record)
    return record['batch_id']


def save_triggered_at(instance, **kwargs):
    db = instance.db
    log_collection = instance.log_collection
    w_triggered_by = instance.w_triggered_by

    record = {
        'triggered_at': instance.triggered_at,
        'triggered_by': instance.w_triggered_by,
        'batch_id': instance.batch_id
    }

    if w_triggered_by.endswith('_list'):
        record['records_count'] = kwargs['records_count']
        record['target'] = instance.target
    elif w_triggered_by.endswith('_deatil'):
        record['records_count'] = kwargs['records_count']
    elif w_triggered_by == 'match':
        record['records_count'] = kwargs['records_count']
        record['matched_count'] = kwargs['matched_count']
    elif w_triggered_by == 'place':
        record['update_found_count'] = kwargs['update_found_count']
        record['update_not_found_count'] = kwargs['update_not_found_count']
        record['api_found'] = kwargs['api_found']
        record['api_not_found'] = kwargs['api_not_found']
    # pprint.pprint(record)
    db[log_collection].insert_one(record)


def selenium_wait_js_load():
    time.sleep(10)


def selenium_wait_all_diners_load():
    time.sleep(20)


def selenium_wait_btn_show(driver, locator):
    return WebDriverWait(driver, 40, 0.5).until(EC.presence_of_element_located(locator))


def dispatch_diners_lambda(diners_count):
    lamdas_count = 14
    divider = diners_count // lamdas_count
    print('Now each get_detail will fetch ', divider, ' results.')
    offsets = [i * divider for i in range(lamdas_count)]
    limits = [divider for i in range(lamdas_count - 1)]
    remainder = diners_count - offsets[-1]
    limits.append(remainder)
    sleep_list = [i for i in range(lamdas_count)]
    indexes = [{
        'offset': offsets[i],
        'limit': limits[i],
        'sleep': sleep_list[i]
    } for i in range(lamdas_count)]

    return indexes


class DinerDispatcher():
    def __init__(self,
                 db,
                 read_collection,
                 write_collection,
                 log_collection,
                 r_triggered_by,
                 offset=0,
                 limit=0):
        self.db = db
        self.read_collection = read_collection
        self.write_collection = write_collection
        self.log_collection = log_collection
        self.r_triggered_by = r_triggered_by
        self.triggered_at = get_triggered_at(self)
        self.diners_cursor = get_diners_cursor(self, offset, limit)

    def main(self):
        db = self.db
        write_collection = self.write_collection
        diners_cursor = self.diners_cursor
        db[write_collection].drop()
        records = []
        diners_count = 0
        for diner in diners_cursor:
            record = InsertOne(diner)
            records.append(record)
            diners_count += 1
        db[write_collection].bulk_write(records)
        print('There are ', diners_count, ' diners in ', write_collection, '.')
        return diners_count


class Checker():
    def __init__(self, db, read_collection, log_collection, r_triggered_by):
        self.db = db
        self.read_collection = read_collection
        self.log_collection = log_collection
        self.r_triggered_by = r_triggered_by
        self.triggered_at = self.get_triggered_at()

    def get_triggered_at(self):
        db = self.db
        log_collection = self.log_collection
        pipeline = [{
            '$match': {
                'triggered_by': self.r_triggered_by
            }
        }, {
            '$sort': {
                'triggered_at': 1
            }
        }, {
            '$group': {
                '_id': None,
                'triggered_at': {
                    '$last': '$triggered_at'
                }
            }
        }]
        cursor = db[log_collection].aggregate(pipeline=pipeline)
        result = next(cursor)['triggered_at']
        cursor.close()
        return result

    def get_batch_id(self):
        db = self.db
        log_collection = self.log_collection
        pipeline = [{
            '$match': {
                'triggered_by': self.r_triggered_by
            }
        }, {
            '$sort': {
                'triggered_at': 1
            }
        }, {
            '$group': {
                '_id': None,
                'batch_id': {
                    '$last': '$batch_id'
                }
            }
        }]
        cursor = db[log_collection].aggregate(pipeline=pipeline)
        result = next(cursor)['batch_id']
        cursor.close()
        return result

    def get_latest_records_cursor(self, limit=0):
        db = self.db
        read_collection = self.read_collection
        triggered_at = self.triggered_at
        pipeline = [{
            '$match': {
                'title': {
                    "$exists": True
                },
                'triggered_at': triggered_at
            }
        }, {
            '$sort': {
                'uuid': 1
            }
        }]
        if limit > 0:
            pipeline.append({'$limit': limit})
        cursor = db[read_collection].aggregate(pipeline=pipeline,
                                               allowDiskUse=True)
        return cursor

    def get_latest_records_count(self):
        db = self.db
        read_collection = self.read_collection
        triggered_at = self.triggered_at
        pipeline = [{
            '$match': {
                'title': {
                    "$exists": True
                },
                'triggered_at': triggered_at
            }
        }, {
            '$count': 'triggered_at'
        }]
        cursor = db[read_collection].aggregate(pipeline=pipeline,
                                               allowDiskUse=True)
        result = next(cursor)['triggered_at']
        return result

    def get_latest_errorlogs(self):
        db = self.db
        read_collection = self.read_collection
        triggered_at = self.get_triggered_at()
        pipeline = [{
            '$match': {
                'title': {
                    "$exists": False
                },
                'triggered_at': triggered_at
            }
        }]
        cursor = db[read_collection].aggregate(pipeline=pipeline,
                                               allowDiskUse=True)
        return cursor

    def check_records(self, cursor, fields, data_range):
        loop_count = 0
        for record in cursor:
            if loop_count > data_range:
                break
            pprint.pprint([record[field] for field in fields])
            loop_count += 1


if __name__ == '__main__':
    print('a')
    # MONGO_EC2_URI = env.MONGO_EC2_URI
    # admin_client = MongoClient(MONGO_EC2_URI)
    # db = admin_client['ufc']
    # dispatcher = DinerDispatcher(db,
    #                              read_collection='fp_list',
    #                              write_collection='fp_list_temp',
    #                              log_collection='trigger_log',
    #                              r_triggered_by='get_fp_list')
    # print(dispatcher.triggered_at)
    # dispatcher.target = read_json('target_fp.json')
    # dispatcher.batch_id = 0
    # save_triggered_at(dispatcher, records_count=1)
    # checker = Checker(db,
    #                   read_collection='fp_list',
    #                   log_collection='trigger_log',
    #                   r_triggered_by='get_fp_list')
    # cursor = checker.get_latest_errorlogs()
    # pprint.pprint(next(cursor))
