from django.shortcuts import render
# from django.http import HttpResponse
from rest_framework import views
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .serializers import MatchSerializer, FilterSerializer
# from django.db import transaction
# from rest_framework.generics import GenericAPIView
from .models import MatchChecker, MatchFilters, MatchSearcher, MatchDinerInfo, Pipeline
import env
from pymongo import MongoClient
import time
import pprint
# import requests
# import json
# from . import models
# Create your views here.
MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc_temp']
match_checker = MatchChecker(db, 'matched', 'match')
match_searcher = MatchSearcher(db, 'matched')
match_dinerinfo = MatchDinerInfo(db, 'matched')
match_filters = MatchFilters(db, 'matched')


class DinerList(views.APIView):
    parser_classes = [JSONParser]

    def get(self, request):
        start = time.time()
        offset_param = self.request.query_params.get('offset', None)
        if offset_param:
            offset = int(offset_param)
        else:
            offset = 0
        diners = match_checker.get_latest_records(Pipeline.ue_list_pipeline, offset, limit=6)
        diners_count = match_checker.get_count(Pipeline.ue_count_pipeline)
        if offset + 6 < diners_count:
            has_more = True
        else:
            has_more = False
        if has_more:
            next_offset = offset + 6
        else:
            next_offset = 0
        diners = [diner['_id'] for diner in diners]
        data = MatchSerializer(diners, many=True).data
        stop = time.time()
        print('get DinerList took: ', stop - start, 's.')
        return Response({
            'next_offset': next_offset,
            'has_more': has_more,
            'max_page': diners_count // 6,
            'data_count': len(diners),
            'data': data
            })


class DinerSearch(views.APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        start = time.time()
        condition = request.data['condition']
        pprint.pprint(condition)
        offset = request.data['offset']
        triggered_at = match_checker.triggered_at
        diners, diners_count = match_searcher.get_search_result(condition, triggered_at, offset)
        if offset + 6 < diners_count:
            has_more = True
        else:
            has_more = False
        if has_more:
            next_offset = offset + 6
        else:
            next_offset = 0
        diners = list(diners)
        data = MatchSerializer(diners, many=True).data
        stop = time.time()
        print('post DinerSearch took: ', stop - start, 's.')
        return Response({
            'next_offset': next_offset,
            'has_more': has_more,
            'max_page': diners_count // 6,
            'data_count': len(diners),
            'data': data
            })


class DinerInfo(views.APIView):
    parser_classes = [JSONParser]

    def get(self, request):
        start = time.time()
        uuid_ue = self.request.query_params.get('uuid_ue', None)
        uuid_fp = self.request.query_params.get('uuid_fp', None)
        if uuid_ue:
            triggered_at = match_checker.triggered_at
            diner = match_dinerinfo.get_diner(uuid_ue, 'ue', triggered_at)
            diner = list(diner)[0]
            results = MatchSerializer(diner, many=False).data
            stop = time.time()
            print('get DinerInfo took: ', stop - start, 's.')
            return Response({'data': results})
        if uuid_fp:
            triggered_at = match_checker.triggered_at
            diner = match_dinerinfo.get_diner(uuid_fp, 'fp', triggered_at)
            diner = list(diner)[0]
            results = MatchSerializer(diner, many=False).data
            stop = time.time()
            print('get DinerInfo took: ', stop - start, 's.')
            return Response({'data': results})
        else:
            return Response({'message': 'need diner_id'})


class Filters(views.APIView):
    def get(self, request):
        start = time.time()
        triggered_at = match_checker.triggered_at
        filters = match_filters.get_filters(triggered_at)
        data = FilterSerializer(filters, many=False).data
        stop = time.time()
        print('get DinerInfo took: ', stop - start, 's.')
        return Response({'data': data})


def dinerlist(request):
    return render(request, 'Diner_app/dinerlist.html', {})


def dinerinfo(request):
    # uuid_ue = request.GET.get('uuid_ue')
    # uuid_fp = request.GET.get('uuid_fp')
    # if uuid_ue:
    #     response = requests.get(f'http://localhost:3000/api/v1/dinerinfo?uuid_ue={uuid_ue}').content
    # elif uuid_fp:
    #     response = requests.get(f'http://localhost:3000/api/v1/dinerinfo?uuid_fp={uuid_fp}').content
    # data = json.loads(response)['data']
    return render(request, 'Diner_app/dinerinfo.html', {})
