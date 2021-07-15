# for db control
from pymongo import MongoClient, UpdateOne

# for timing
import time
from datetime import datetime, timedelta

# for compare
from itertools import product
from difflib import SequenceMatcher
from geopy import distance

# for preview
import pprint

# for garbage collect, to avoid memory error
import gc

# home-made modules
# for file handling
import env
import conf

# my utility belt
import utils

MONGO_EC2_URI = env.MONGO_EC2_URI
DB_NAME = conf.DB_NAME

UE_DETAIL_COLLECTION = conf.UE_DETAIL_COLLECTION
FP_DETAIL_COLLECTION = conf.FP_DETAIL_COLLECTION
MATCHED_COLLECTION = conf.MATCHED_COLLECTION

LOG_COLLECTION = conf.LOG_COLLECTION
GET_UE_DETAIL = conf.GET_UE_DETAIL
GET_FP_DETAIL = conf.GET_FP_DETAIL
MATCH = conf.MATCH

admin_client = MongoClient(MONGO_EC2_URI)

db = admin_client[DB_NAME]


class Match():
    def __init__(self,
                 db,
                 read_collection_ue,
                 read_collection_fp,
                 write_collection,
                 log_collection,
                 w_triggered_by,
                 triggered_by_ue,
                 triggered_by_fp,
                 triggered_at,
                 limit=0):
        self.db = db
        self.read_collection_ue = read_collection_ue
        self.read_collection_fp = read_collection_fp
        self.write_collection = write_collection
        self.log_collection = log_collection
        self.w_triggered_by = w_triggered_by
        self.triggered_by_ue = triggered_by_ue
        self.triggered_by_fp = triggered_by_fp
        self.triggered_at = triggered_at
        self.limit = limit

    def get_records(self):
        uechecker = utils.Checker(self.db, self.read_collection_ue,
                                  self.log_collection, self.triggered_by_ue)
        ue_cursor = uechecker.get_latest_records_cursor()
        records_ue = list(ue_cursor)
        ue_cursor.close()
        fpchecker = utils.Checker(self.db, self.read_collection_fp,
                                  self.log_collection, self.triggered_by_fp)
        fp_cursor = fpchecker.get_latest_records_cursor()
        records_fp = list(fp_cursor)
        fp_cursor.close()
        return records_ue, records_fp

    def filter_need_compare_records(self, records):
        needed_fields = ['uuid', 'title', 'gps', 'item_pair']
        filtered_records = []
        for record in records:
            filtered_record = {i: record[i] for i in needed_fields}
            filtered_records.append(filtered_record)
        return filtered_records

    def compare(self, records_ue, records_fp):
        records_ue = self.filter_need_compare_records(records_ue)
        records_fp = self.filter_need_compare_records(records_fp)
        gc.collect()
        all_combinations = product(records_ue, records_fp)
        similarities = []
        similar_count = 0
        # log = []
        for ue, fp in all_combinations:
            gps_ue = tuple(ue['gps'])
            gps_fp = tuple(fp['gps'])
            meter = distance.distance(gps_ue, gps_fp).meters
            if meter > 50:
                continue
            else:
                if meter > 0:
                    meter_similarity = (50 - meter) / 50
                else:
                    meter_similarity = 1
                title_ue = ue['title']
                title_fp = fp['title']
                match = SequenceMatcher(lambda x: x == "-", title_ue, title_fp)
                title_similarity = match.ratio()
                similarity = meter_similarity + title_similarity
                if similarity > 1.4:
                    cheaper_ue, cheaper_fp = self.compare_item(ue, fp)
                    similarities.append((ue['uuid'], fp['uuid'], similarity,
                                         cheaper_ue, cheaper_fp))
                    similar_count += 1
                    # log.append([ue['title'], fp['title'], similarity, cheaper_ue, cheaper_fp])
                else:
                    continue
        print('There are ', similar_count, ' similar diners')
        # pprint.pprint(log)
        return similarities, similar_count

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
                cheaper_fp.append(
                    [item_fp, int(item_price_ue - item_price_fp)])
            elif (item_price_ue - item_price_fp < 0):
                cheaper_ue.append(
                    [item_ue, int(item_price_fp - item_price_ue)])
        return cheaper_ue, cheaper_fp

    def transfer_records(self, records, source):
        if source == 'ue':
            op = '_fp'
        else:
            op = '_ue'
        source = '_' + source
        new_records = {}
        list_fields = [
            'tags_ue', 'gps_ue', 'open_days_ue', 'open_hours_ue', 'tags_fp',
            'gps_fp', 'open_days_fp', 'open_hours_fp'
        ]
        int_fields = [
            'deliver_fee_ue', 'deliver_time_ue', 'budget_ue', 'view_count_ue',
            'deliver_fee_fp', 'deliver_time_fp', 'budget_fp', 'view_count_fp'
        ]
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

    def get_max_similarities(self, similarites):
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
                    max_similarities[uuid_ue] = (uuid_fp, sim_new, cheaper_ue,
                                                 cheaper_fp)
            else:
                max_similarities[uuid_ue] = (uuid_fp, sim_new, cheaper_ue,
                                             cheaper_fp)
        return max_similarities

    def parse_filters(self, max_similarities):
        matched_ue_set = set()
        matched_fp_set = set()
        matched_info_dict = {}
        for key in max_similarities:
            uuid_ue = key
            uuid_fp = max_similarities[key][0]
            sim = max_similarities[key][1]
            cheaper_ue = max_similarities[key][2]
            cheaper_fp = max_similarities[key][3]
            matched_ue_set.add(uuid_ue)
            matched_fp_set.add(uuid_fp)
            matched_info_dict[(uuid_ue, uuid_fp)] = (sim, cheaper_ue,
                                                     cheaper_fp)

        return matched_ue_set, matched_fp_set, matched_info_dict

    def remove_matched(self, records_ue, records_fp, matched_ue_set,
                       matched_fp_set):
        records_unmatched = {}
        records_unmatched.update(records_ue)
        records_unmatched.update(records_fp)

        for matched_ue in matched_ue_set:
            del records_unmatched[(matched_ue, '')]
        for matched_fp in matched_fp_set:
            del records_unmatched[('', matched_fp)]
        for key in records_unmatched:
            records_unmatched[key]['similarity'] = 0
            records_unmatched[key]['cheaper_ue'] = []
            records_unmatched[key]['cheaper_fp'] = []

        return records_unmatched

    def combine_records(self, records_ue, records_fp, records_unmatched,
                        matched_info_dict):
        records_dict = records_unmatched
        for key in matched_info_dict:
            uuid_ue = key[0]
            uuid_fp = key[1]
            record_ue = records_ue[(uuid_ue, '')]
            record_fp = records_fp[('', uuid_fp)]
            record = {}
            ue_keys = list(record_ue.keys())
            for ue_key in ue_keys:
                if ('_fp' in ue_key):
                    del record_ue[ue_key]
            fp_keys = list(record_fp.keys())
            for fp_key in fp_keys:
                if ('_ue' in fp_key):
                    del record_fp[fp_key]
            record.update(record_ue)
            record.update(record_fp)
            record['similarity'] = matched_info_dict[key][0]
            record['cheaper_ue'] = matched_info_dict[key][1]
            record['cheaper_fp'] = matched_info_dict[key][2]
            records_dict[key] = record
        return records_dict

    def merge_records(self, records_ue, records_fp, similarites):
        max_similarities = self.get_max_similarities(similarites)

        matched_ue_set, matched_fp_set, matched_info_dict = self.parse_filters(
            max_similarities)
        # matched_ue_set and matched_fp_set will be used to remove those diner who has matched
        # so when records_ue and records_fp merged, there won't be duplicate diner
        # after merged, will use matched_info_dict to add those diner back

        records_ue = self.transfer_records(records_ue, 'ue')
        records_fp = self.transfer_records(records_fp, 'fp')
        records_unmatched = self.remove_matched(records_ue, records_fp,
                                                matched_ue_set, matched_fp_set)
        # records_unmatched is records without matched

        records_dict = self.combine_records(records_ue, records_fp,
                                            records_unmatched,
                                            matched_info_dict)
        # this function will combine records_unmatched with matched records

        return records_dict

    def save_to_matched(self, records_dict):
        db = self.db
        write_collection = self.write_collection
        triggered_at = self.triggered_at
        records = []

        for key in records_dict:
            diner = records_dict[key]
            diner['triggered_at'] = triggered_at
            records.append(diner)

        diners_count = len(records)
        slice_count = 10
        divider = diners_count // slice_count
        limits = [divider for i in range(slice_count - 1)]
        offsets = [i * divider for i in range(slice_count)]
        remainder = diners_count - offsets[-1]
        limits.append(remainder)
        indexes = [{
            'offset': offsets[i],
            'limit': limits[i]
        } for i in range(slice_count)]

        for index in indexes:
            offset = index['offset']
            limit = index['limit']
            record_slice = records[offset:offset + limit]
            print('Going to save ', len(record_slice),
                  'diners to db.matched in this slice.')
            upsert_records = []
            for diner in record_slice:
                record = UpdateOne(
                    {
                        'uuid_ue': diner['uuid_ue'],
                        'uuid_fp': diner['uuid_fp'],
                        'triggered_at_ue': diner['triggered_at_ue'],
                        'triggered_at_fp': diner['triggered_at_fp'],
                        'triggered_at': triggered_at
                    }, {'$set': diner},
                    upsert=True)
                upsert_records.append(record)
            db[write_collection].bulk_write(upsert_records)
            gc.collect()
        print('Totally save ', len(records),
              'diners to db.matched in this slice.')
        pprint.pprint('write into matched successed')
        return len(records)

    def remove_old_records(self):
        db = self.db
        triggered_at = self.triggered_at
        last_week = triggered_at - timedelta(weeks=2)
        db.ue_detail.delete_many({"triggered_at": {"$lt": last_week}})
        db.fp_detail.delete_many({"triggered_at": {"$lt": last_week}})
        db.matched.delete_many({"triggered_at": {"$lt": last_week}})

    def main(self):
        print('Start comparsion, using', self.triggered_at, "'s records.")

        p_start = time.time()
        self.batch_id = utils.save_start_at(self)
        records_ue, records_fp = self.get_records()
        limit = self.limit
        if limit == 0:
            pass
        else:
            records_ue = records_ue[:limit]
            records_fp = records_fp[:limit]

        c_start = time.time()
        similarities, matched_count = self.compare(records_ue, records_fp)
        c_stop = time.time()
        print('compare took: ', c_stop - c_start)

        records_dict = self.merge_records(records_ue, records_fp, similarities)
        del records_ue
        del records_fp
        del similarities
        gc.collect()

        p_stop = time.time()
        print('process took: ', p_stop - p_start)

        s_start = time.time()
        records_count = self.save_to_matched(records_dict)
        utils.save_triggered_at(self,
                                records_count=records_count,
                                matched_count=matched_count)
        s_stop = time.time()
        print('save to db took: ', s_stop - s_start)
        self.remove_old_records()


if __name__ == '__main__':
    limit = 400
    triggered_at = datetime(2021, 6, 16, 12, 0)
    matcher = Match(db,
                    read_collection_ue=UE_DETAIL_COLLECTION,
                    read_collection_fp=FP_DETAIL_COLLECTION,
                    write_collection=MATCHED_COLLECTION,
                    log_collection=LOG_COLLECTION,
                    w_triggered_by=MATCH,
                    triggered_by_ue=GET_UE_DETAIL,
                    triggered_by_fp=GET_FP_DETAIL,
                    triggered_at=triggered_at,
                    limit=limit)
    matcher.main()

    read_collection = 'matched'
    triggered_by = 'match'
    checker = utils.Checker(db,
                            read_collection=MATCHED_COLLECTION,
                            log_collection=LOG_COLLECTION,
                            r_triggered_by=MATCH)
    cursor = checker.get_latest_records_cursor(1)
    for record in cursor:
        pprint.pprint(record)
        pprint.pprint(record.keys())
    cursor.close()
