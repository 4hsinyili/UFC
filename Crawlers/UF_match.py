from datetime import datetime, timedelta
from Crawlers.FP_crawl import FPChecker
from Crawlers.UE_crawl import UEChecker
from pymongo import MongoClient, UpdateOne
import env
from itertools import product
from difflib import SequenceMatcher
from geopy import distance
import time
import pprint
import gc

MONGO_EC2_URI = env.MONGO_EC2_URI
admin_client = MongoClient(MONGO_EC2_URI)

db = admin_client['ufc']


class Match():
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection
        self.triggered_at = self.get_triggered_at()

    def get_triggered_at(self, collection='stepfunction_log'):
        db = self.db
        pipeline = [
            {
                '$sort': {'ue_triggered_at': 1}
            },
            {
                '$group': {
                    '_id': None,
                    'triggered_at': {'$last': '$ue_triggered_at'}
                    }
            }
        ]
        cursor = db[collection].aggregate(pipeline=pipeline)
        result = next(cursor)['triggered_at']
        return result

    def get_records(self):
        db = self.db
        uechecker = UEChecker(db, 'ue_detail', 'get_ue_detail')
        ue_cursor = uechecker.get_last_records()
        ue_records = list(ue_cursor)
        for ue_record in ue_records:
            ue_record['choice'] = ue_record['UE_choice']
            del ue_record['UE_choice']
        ue_cursor.close()
        fpchecker = FPChecker(db, 'fp_detail', 'get_fp_detail')
        fp_cursor = fpchecker.get_last_records()
        fp_records = list(fp_cursor)
        for fp_record in fp_records:
            fp_record['choice'] = fp_record['FP_choice']
            del fp_record['FP_choice']
        fp_cursor.close()
        return ue_records, fp_records

    def filter_need_compare_records(self, records):
        needed_fields = ['uuid', 'title', 'gps', 'item_pair']
        filtered_records = []
        for record in records:
            filtered_record = {i: record[i] for i in needed_fields}
            filtered_records.append(filtered_record)
        return filtered_records

    def compare(self, ue_records, fp_records):
        ue_records = self.filter_need_compare_records(ue_records)
        fp_records = self.filter_need_compare_records(fp_records)
        gc.collect()
        all_combinations = product(ue_records, fp_records)
        similarities = []
        loop_count = 0
        log = []
        for ue, fp in all_combinations:
            gps_ue = tuple(ue['gps'])
            gps_fp = tuple(fp['gps'])
            meter = distance.distance(gps_ue, gps_fp).meters
            if meter > 50:
                continue
            else:
                if meter > 0:
                    meter_similarity = (50-meter) / 50
                else:
                    meter_similarity = 1
                title_ue = ue['title']
                title_fp = fp['title']
                match = SequenceMatcher(lambda x: x == "-", title_ue, title_fp)
                title_similarity = match.ratio()
                similarity = meter_similarity + title_similarity
                if similarity > 1.4:
                    cheaper_ue, cheaper_fp = self.compare_item(ue, fp)
                    similarities.append((ue['uuid'], fp['uuid'], similarity, cheaper_ue, cheaper_fp))
                    loop_count += 1
                    log.append([ue['title'], fp['title'], similarity, cheaper_ue, cheaper_fp])
                else:
                    continue
        print('There are ', loop_count, ' similar diners')
        # pprint.pprint(log)
        return similarities, loop_count

    def compare_item(self, ue_record, fp_record):
        cheaper_ue = []
        cheaper_fp = []
        item_pair_ue = ue_record['item_pair']
        item_pair_fp = fp_record['item_pair']
        all_combinations = product(item_pair_ue.keys(), item_pair_fp.keys())
        for item_ue, item_fp in all_combinations:
            if item_ue != item_fp:
                continue
            item_price_ue = item_pair_ue[item_ue]
            item_price_fp = item_pair_fp[item_fp]
            if (item_price_ue - item_price_fp > 0):
                cheaper_fp.append([item_fp, int(item_price_ue - item_price_fp)])
            elif (item_price_ue - item_price_fp < 0):
                cheaper_ue.append([item_ue, int(item_price_fp - item_price_ue)])
        return cheaper_ue, cheaper_fp

    def transfer_records(self, records, source):
        if source == 'ue':
            op = 'fp'
        else:
            op = 'ue'
        source = '_' + source
        op = '_' + op
        new_records = {}
        list_fields = ['tags_ue', 'gps_ue', 'open_days_ue', 'open_hours_ue', 'tags_fp', 'gps_fp', 'open_days_fp', 'open_hours_fp']
        int_fields = ['deliver_fee_ue', 'deliver_time_ue', 'budget_ue', 'view_count_ue', 'deliver_fee_fp', 'deliver_time_fp', 'budget_fp', 'view_count_fp']
        float_fields = ['rating_ue', 'rating_fp']
        dict_fields = ['menu_ue', 'menu_fp']
        bool_fields = ['choice_ue', 'choice_fp']
        datetime_fields = ['triggered_at_ue', 'triggered_at_fp']
        for record in records:
            del record['item_pair']
            keys = list(record.keys())
            new_keys = [i + source for i in keys]
            for new_key in new_keys:
                record[new_key] = record[new_key.replace(source, '')]
                del record[new_key.replace(source, '')]

                new_key_op = new_key.replace(source, op)
                if new_key_op in list_fields:
                    record[new_key_op] = []
                elif new_key_op in int_fields:
                    record[new_key_op] = 0
                elif new_key_op in float_fields:
                    record[new_key_op] = 0
                elif new_key_op in dict_fields:
                    record[new_key_op] = {}
                elif new_key_op in bool_fields:
                    record[new_key_op] = False
                elif new_key_op in datetime_fields:
                    record[new_key_op] = datetime.min
                else:
                    record[new_key_op] = ''
            new_records[(record['uuid_ue'], record['uuid_fp'])] = record
        return new_records

    def merge_records(self, records_ue, records_fp, similarites):
        max_similarities = {}
        for similarity in similarites:
            uuid_ue = similarity[0]
            uuid_fp = similarity[1]
            sim_new = similarity[2]
            cheaper_ue = similarity[3]
            cheaper_fp = similarity[4]
            if uuid_ue in max_similarities.keys():
                sim_old = max_similarities[uuid_ue][1]
                if sim_new > sim_old:
                    max_similarities[uuid_ue] = (uuid_fp, sim_new, cheaper_ue, cheaper_fp)
            else:
                max_similarities[uuid_ue] = (uuid_fp, sim_new, cheaper_ue, cheaper_fp)
        similarities_ue = set()
        similarities_fp = set()
        similarities_mathced = {}
        for key in max_similarities:
            uuid_ue = key
            uuid_fp = max_similarities[key][0]
            sim = max_similarities[key][1]
            cheaper_ue = max_similarities[key][2]
            cheaper_fp = max_similarities[key][3]
            similarities_ue.add(uuid_ue)
            similarities_fp.add(uuid_fp)
            similarities_mathced[(uuid_ue, uuid_fp)] = (sim, cheaper_ue, cheaper_fp)
        records_ue = self.transfer_records(records_ue, 'ue')
        records_fp = self.transfer_records(records_fp, 'fp')
        records_combined = {}
        records_combined.update(records_ue)
        records_combined.update(records_fp)
        for key in similarities_ue:
            del records_combined[(key, '')]
        for key in similarities_fp:
            del records_combined[('', key)]
        for key in records_combined:
            records_combined[key]['uuid_gm'] = ''
            records_combined[key]['similarity'] = 0
            records_combined[key]['cheaper_ue'] = []
            records_combined[key]['cheaper_fp'] = []
        for key in similarities_mathced:
            uuid_ue = key[0]
            uuid_fp = key[1]
            record_ue = records_ue[(uuid_ue, '')]
            record_fp = records_fp[('', uuid_fp)]
            record_matched = {}
            ue_keys = list(record_ue.keys())
            for ue_key in ue_keys:
                if ('_fp' in ue_key):
                    del record_ue[ue_key]
            fp_keys = list(record_fp.keys())
            for fp_key in fp_keys:
                if ('_ue' in fp_key):
                    del record_fp[fp_key]
            record_matched.update(record_ue)
            record_matched.update(record_fp)
            record_matched['similarity'] = similarities_mathced[key][0]
            record_matched['cheaper_ue'] = similarities_mathced[key][1]
            record_matched['cheaper_fp'] = similarities_mathced[key][2]
            records_combined[key] = record_matched
        return records_combined

    def save_to_matched(self, diners):
        db = self.db
        collection = self.collection
        records = []
        for key in diners:
            diner = diners[key]
            diner['uuid_matched'] = {
                'uuid_fp': diner['uuid_fp'],
                'uuid_ue': diner['uuid_ue']
            }
            if diner['triggered_at_ue'] == datetime.min:
                triggered_at = diner['triggered_at_fp']
            else:
                triggered_at = diner['triggered_at_ue']
            diner['triggered_at'] = triggered_at
            records.append(diner)
        diners_count = len(records)
        slice_count = 10
        divider = diners_count // slice_count
        limits = [divider for i in range(slice_count - 1)]
        offsets = [i * divider for i in range(slice_count)]
        remainder = diners_count - offsets[-1]
        limits.append(remainder)
        indexes = [{'offset': offsets[i], 'limit': limits[i]} for i in range(slice_count)]
        for index in indexes:
            offset = index['offset']
            limit = index['limit']
            record_slice = records[offset: offset+limit]
            print('Going to save ', len(record_slice), 'diners to db.matched in this slice.')
            upsert_records = []
            for diner in record_slice:
                record = UpdateOne(
                    {
                        'uuid_ue': diner['uuid_ue'],
                        'uuid_fp': diner['uuid_fp'],
                        'uuid_matched': diner['uuid_matched'],
                        'triggered_at_ue': diner['triggered_at_ue'],
                        'triggered_at_fp': diner['triggered_at_fp'],
                        'triggered_at': triggered_at
                        }, {'$set': diner}, upsert=True
                )
                upsert_records.append(record)
            db[collection].bulk_write(upsert_records)
            gc.collect()
        print('Totally save ', len(records), 'diners to db.matched in this slice.')
        pprint.pprint('write into matched successed')

    def save_triggered_at(self, records_count, matched_count):
        db = self.db
        triggered_at = self.triggered_at
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'records_count': records_count,
            'matched_count': matched_count,
            'triggered_by': 'match'
            })

    def save_start_at(self):
        db = self.db
        triggered_at = self.triggered_at
        trigger_log = 'trigger_log'
        db[trigger_log].insert_one({
            'triggered_at': triggered_at,
            'triggered_by': 'match_start',
            })

    def remove_old_records(self):
        db = self.db
        triggered_at = self.triggered_at
        last_week = triggered_at - timedelta(weeks=1)
        db.ue_detail.delete_many({"triggered_at": {"$lt": last_week}})
        db.fp_detail.delete_many({"triggered_at": {"$lt": last_week}})
        db.matched.delete_many({"triggered_at": {"$lt": last_week}})

    def main(self, data_range=0):
        self.save_start_at()
        print('Start comparsion, using', self.triggered_at, "'s records.")
        start = time.time()
        ue_records, fp_records = self.get_records()
        if data_range == 0:
            pass
        else:
            ue_records = ue_records[:data_range]
            fp_records = fp_records[:data_range]
        c_start = time.time()
        similarities, matched_count = self.compare(ue_records, fp_records)
        c_stop = time.time()
        print('compare took: ', c_stop - c_start)
        matched_records = self.merge_records(ue_records, fp_records, similarities)
        del ue_records
        del fp_records
        del similarities
        gc.collect()
        records_count = len(list(matched_records.keys()))
        stop = time.time()
        print('process took: ', stop - start)
        self.save_to_matched(matched_records)
        self.save_triggered_at(records_count, matched_count)
        # self.remove_old_records()


class MatchedChecker():
    def __init__(self, db, collection, triggered_by):
        self.db = db
        self.collection = collection
        self.triggered_by = triggered_by
        self.triggered_at = self.get_triggered_at()

    def get_triggered_at(self, collection='trigger_log'):
        db = self.db
        pipeline = [
            {
                '$match': {'triggered_by': self.triggered_by}
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
        cursor = db[collection].aggregate(pipeline=pipeline)
        result = next(cursor)['triggered_at']
        cursor.close()
        return result

    def get_last_records(self, limit=0):
        db = self.db
        collection = self.collection
        triggered_at = self.get_triggered_at()
        pipeline = [
            {'$match': {
                'triggered_at': triggered_at
                }}, {
                '$sort': {'uuid_ue': 1}
                }
        ]
        if limit > 0:
            pipeline.append({'$limit': limit})
        cursor = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return cursor


if __name__ == '__main__':
    collection = 'matched'
    data_range = 0
    matcher = Match(db, collection)
    # matcher.remove_old_records()
    # print(matcher.triggered_at)
    matcher.main(data_range)
    # checker = MatchedChecker(db, collection, 'match')
    # print(checker.triggered_at)
    # records = checker.get_last_records(1)
    # for record in records:
    #     pprint.pprint(record)
    #     pprint.pprint(record.keys())
