from django.shortcuts import render
# from django.http import HttpResponse
from rest_framework import views
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .serializers import UESerializer, FilterSerializer
# from django.db import transaction
# from rest_framework.generics import GenericAPIView
from .models import UEChecker, UESearcher, UEDinerInfo, Pipeline
import env
from pymongo import MongoClient
import time
# import pprint
import requests
import json
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
uechecker = UEChecker(db, 'ue_detail')
uesearcher = UESearcher(db, 'ue_detail')
uedinerinfo = UEDinerInfo(db, 'ue_detail')


class DinerList(views.APIView):
    parser_classes = [JSONParser]

    def get(self, request):
        start = time.time()
        offset_param = self.request.query_params.get('offset', None)
        if offset_param:
            offset = int(offset_param)
        else:
            offset = 0
        diners = uechecker.get_last_records(Pipeline.ue_list_pipeline, offset, limit=6)
        diners_count = uechecker.get_count(Pipeline.ue_count_pipeline)
        if offset + 6 < diners_count:
            has_more = True
        else:
            has_more = False
        if has_more:
            next_offset = offset + 6
        else:
            next_offset = 0
        diners = [diner['_id'] for diner in diners]
        data = UESerializer(diners, many=True).data
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
        offset = request.data['offset']
        diners = uesearcher.get_search_result(condition, offset)
        diners_count = uechecker.get_count(Pipeline.ue_count_pipeline)
        if offset + 6 < diners_count:
            has_more = True
        else:
            has_more = False
        if has_more:
            next_offset = offset + 6
        else:
            next_offset = 0
        diners = list(diners)
        data = UESerializer(diners, many=True).data
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
        diner_id = self.request.query_params.get('diner_id', None)
        if diner_id:
            diners = uedinerinfo.get_diner(diner_id)
            diners = list(diners)[0]
            results = UESerializer(diners, many=False).data
            stop = time.time()
            print('get DinerInfo took: ', stop - start, 's.')
            return Response({'data': results})
        else:
            return Response({'message': 'need diner_id'})


class Filters(views.APIView):
    def get(self, request):
        start = time.time()
        filters = uechecker.get_filters()
        data = FilterSerializer(filters, many=False).data
        stop = time.time()
        print('get DinerInfo took: ', stop - start, 's.')
        return Response({'data': data})


def dinerlist(request):
    return render(request, 'Diner_app/dinerlist.html', {})


def dinerinfo(request):
    diner_id = request.GET.get('diner_id')
    response = requests.get(f'http://localhost:3000/api/v1/dinerinfo?diner_id={diner_id}').content
    data = json.loads(response)['data']
    data['view_count'] = int(data['view_count'])
    return render(request, 'Diner_app/diner.html', {'data': data})