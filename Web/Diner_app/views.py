from django.shortcuts import render, redirect
# from django.http import HttpResponse
from rest_framework import views
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .serializers import MatchSerializer, FilterSerializer
# from django.db import transaction
# from rest_framework.generics import GenericAPIView
from .models import MatchChecker, MatchFilters, MatchSearcher, MatchDinerInfo, Favorites, Pipeline
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
favorites_model = Favorites(db, 'favorites')


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
        user_id = request.data['user_id']
        offset = request.data['offset']
        triggered_at = match_checker.triggered_at
        if user_id > 0:
            diners, diners_count = match_searcher.get_search_result(condition, triggered_at, offset, user_id, favorites_model)
        else:
            diners, diners_count = match_searcher.get_search_result(condition, triggered_at, offset)
        if offset + 6 < diners_count:
            has_more = True
        else:
            has_more = False
        if has_more:
            next_offset = offset + 6
        else:
            next_offset = 0
        diners = diners
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


class DinerShuffle(views.APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        start = time.time()
        user_id = request.data['user_id']
        triggered_at = match_checker.triggered_at
        if user_id > 0:
            diners = match_searcher.get_random(triggered_at, user_id, favorites_model)
        else:
            diners = match_searcher.get_random(triggered_at)
        has_more = False
        next_offset = 0
        diners = diners
        data = MatchSerializer(diners, many=True).data
        stop = time.time()
        print('post DinerSearch took: ', stop - start, 's.')
        return Response({
            'next_offset': next_offset,
            'has_more': has_more,
            'max_page': 1,
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


class FavoritesAPI(views.APIView):
    def post(self, request):
        request_data = request.data
        user_id = request_data['user_id']
        source = request_data['source']
        if source == 'ue':
            uuid = request_data['uuid_ue']
        if source == 'fp':
            uuid = request_data['uuid_fp']
        activate = request_data['activate']
        print(user_id, uuid, source, activate)
        favorites_model.change_favorites(user_id, uuid, source, activate)
        return Response({'message': 'success'})

    def get(self, request):
        user_id = int(self.request.query_params.get('user_id', None))
        offset = int(self.request.query_params.get('offset', None))
        favorites = favorites_model.get_favorites(user_id)
        favorites_count = len(favorites)
        if favorites_count == 0:
            return Response({
                'is_data': False
            })
        diners = []
        triggered_at = match_checker.triggered_at
        if offset + 6 < favorites_count:
            has_more = True
        else:
            has_more = False
        if has_more:
            next_offset = offset + 6
        else:
            next_offset = 0
        for favorite in favorites[offset: offset+6]:
            if len(favorite) > 8:
                uuid_ue = favorite
                result = match_dinerinfo.get_diner(uuid_ue, 'ue', triggered_at)
                try:
                    diner = next(result)
                    diner['favorite'] = True
                    diners.append(diner)
                except Exception:
                    pass
            else:
                uuid_fp = favorite
                result = match_dinerinfo.get_diner(uuid_fp, 'fp', triggered_at)
                try:
                    diner = next(result)
                    diner['favorite'] = True
                    diners.append(diner)
                except Exception:
                    pass
        if len(diners) == 0:
            return Response({
                'is_data': False
            })
        data = MatchSerializer(diners, many=True).data
        return Response({
            'is_data': True,
            'next_offset': next_offset,
            'has_more': has_more,
            'max_page': 1,
            'data_count': len(diners),
            'data': data
            })


def dinerlist(request):
    user_id = request.user.id
    if user_id is None:
        user_id = 0
    return render(request, 'Diner_app/dinerlist.html', {'user_id': user_id})


def dinerinfo(request):
    return render(request, 'Diner_app/dinerinfo.html', {})


def collection(request):
    user_id = request.user.id
    if user_id is None:
        user_id = 0
    if request.user.is_authenticated:
        return render(request, 'Diner_app/collection.html', {'user_id': user_id})
    else:
        return redirect('login')
