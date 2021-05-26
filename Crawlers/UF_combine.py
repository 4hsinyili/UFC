from Crawlers.FP_crawl import FPChecker
from Crawlers.UE_crawl import UEChecker
from pymongo import MongoClient, UpdateOne
import env
import pandas as pd
from itertools import product
from difflib import SequenceMatcher
from geopy import distance
import time


MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)

db = admin_client['ufc_temp']


class Comparison():
    def compare(self, dict_ue, dict_fp):
        all_combinations = product(dict_ue, dict_fp)
        similarities = []
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
                    similarities.append((ue['uuid'], fp['uuid'], similarity))
                else:
                    continue
        return similarities

    def check_similarity(self, df_ue, df_fp, similarities):
        df_ue = df_ue.set_index('uuid')
        df_fp = df_fp.set_index('uuid')
        for similarity in similarities:
            ue_key = similarity[0]
            fp_key = similarity[1]
            title_ue = df_ue.loc[ue_key, 'title']
            title_fp = df_fp.loc[fp_key, 'gps']
            link_ue = df_ue.loc[ue_key, 'title']
            link_fp = df_fp.loc[fp_key, 'gps']
            print(title_ue, title_fp)
            print(link_ue, link_fp)

    def add_id(self, similarities, df_ue, df_fp):
        df_ue = df_ue.set_index('uuid', drop=False)
        df_fp = df_fp.set_index('uuid', drop=False)
        df_ue = df_ue.rename(columns={'uuid': 'uuid_ue'})
        df_fp = df_fp.rename(columns={'uuid': 'uuid_fp'})
        df_ue['similarity'] = 0
        df_fp['similarity'] = 0
        df_ue['fp_key'] = ''
        df_fp['ue_key'] = ''
        for similarity in similarities:
            ue_key = similarity[0]
            fp_key = similarity[1]
            similarity_value = similarity[2]
            df_ue_cs = df_ue.loc[ue_key, 'similarity']
            df_fp_cs = df_fp.loc[fp_key, 'similarity']
            if (similarity_value > df_ue_cs) and (similarity_value > df_fp_cs):
                df_ue.loc[ue_key, 'fp_key'] = fp_key
                df_fp.loc[fp_key, 'ue_key'] = ue_key
                df_ue.loc[ue_key, 'similarity'] = similarity_value
        return df_ue, df_fp

    def merge_ue_fp(self, df_ue, df_fp):
        df_u_f = df_ue.merge(df_fp, left_on='uuid_ue', right_on='ue_key', how='outer', suffixes=('_ue', '_fp'))
        try:
            df_u_f['similarity'].fillna(0, inplace=True)
            print('similarity')
        except Exception:
            df_u_f['similarity_ue'].fillna(0, inplace=True)
            print('similarity_ue')
        return df_u_f

    def get_dfs(self):
        uechecker = UEChecker(db, 'ue_detail')
        ue_result = uechecker.get_last_records()
        ue_result = list(ue_result)

        fpchecker = FPChecker(db, 'fp_detail')
        fp_result = fpchecker.get_last_records()
        fp_result = list(fp_result)

        df_ue = pd.DataFrame(ue_result)
        df_fp = pd.DataFrame(fp_result)
        return df_ue, df_fp

    def turn_dicts(self, df_ue, df_fp):
        dict_ue = df_ue.to_dict('records')
        dict_fp = df_fp.to_dict('records')
        return dict_ue, dict_fp

    def save_to_matched(self, db, collection, df_u_f):
        diners = df_u_f.to_dict('records')
        records = []
        for diner in diners:
            diner['uuid_matched'] = {
                'uuid_fp': diner['uuid_fp'],
                'uuid_ue': diner['uuid_ue']
            }
            if pd.isnull(diner['triggered_at_ue']):
                triggered_at = diner['triggered_at_fp']
            else:
                triggered_at = diner['triggered_at_ue']
            diner['triggered_at'] = triggered_at
            record = UpdateOne(
                {
                    'uuid_ue': diner['uuid_ue'],
                    'uuid_fp': diner['uuid_fp'],
                    'uuid_matched': diner['uuid_matched'],
                    'triggered_at_ue': diner['triggered_at_ue'],
                    'triggered_at_fp': diner['triggered_at_fp'],
                    'triggered_at': triggered_at
                    }, {'$setOnInsert': diner}, upsert=True
            )
            records.append(record)
        db[collection].bulk_write(records)
        print('write into matched successed')

    def correct_types(self, df):
        should_int = ['UE_choice', 'FP_choice', 'budget_ue', 'budget_fp', 'deliver_fee_ue', 'deliver_fee_fp', 'deliver_time_ue', 'deliver_time_fp', 'rating_ue', 'rating_fp', 'view_count_ue', 'view_count_fp']
        for column in df.columns:
            if column in should_int:
                df[column] = df[column].astype('int64')
        return df

    def fill_all_na(self, df):
        for column in df.columns:
            col_type = df[column].dtype
            if col_type == 'int64':
                df[column].fillna(0, inplace=True)
            elif col_type == 'float64':
                df[column].fillna(0, inplace=True)
            elif col_type == 'object':
                df[column].fillna('', inplace=True)
            else:
                df[column].fillna(0, inplace=True)
        return df

    def main(self, db, collection, data_range=0):
        start = time.time()
        df_ue, def_fp = self.get_dfs()
        dict_ue, dict_fp = self.turn_dicts(df_ue, def_fp)
        if data_range == 0:
            pass
        else:
            dict_ue = dict_ue[:data_range]
            dict_fp = dict_fp[:data_range]
        c_start = time.time()
        similarities = self.compare(dict_ue, dict_fp)
        c_stop = time.time()
        df_ue, df_fp = self.add_id(similarities, df_ue, def_fp)
        df_u_f = self.merge_ue_fp(df_ue, df_fp)
        stop = time.time()
        print('process took: ', c_stop - c_start)
        print('compare took: ', stop - start)
        df_u_f = self.fill_all_na(df_u_f)
        df_u_f = self.correct_types(df_u_f)
        print(df_u_f.info())
        self.save_to_matched(db, collection, df_u_f)


class MatchedChecker():
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection

    def get_triggered_at(self):
        collection = self.collection
        pipeline = [
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
        result = db[collection].aggregate(pipeline=pipeline, allowDiskUse=True)
        return result


if __name__ == '__main__':
    collection = 'matched'
    data_range = 0
    comparison = Comparison()
    comparison.main(db, collection, data_range)
