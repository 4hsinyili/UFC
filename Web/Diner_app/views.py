from django.http.response import HttpResponse
from django.shortcuts import render, redirect
# from django.http import HttpResponse
from rest_framework import views
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .serializers import MatchSerializer, FilterSerializer
from django.conf import settings
import os
# from django.db import transaction
# from rest_framework.generics import GenericAPIView
from .models import MatchChecker, MatchFilters, MatchSearcher, MatchDinerInfo, Favorites, Pipeline
import env
from pymongo import MongoClient
import time
import pprint

# Create your views here.
MONGO_HOST = env.MONGO_HOST
MONGO_PORT = env.MONGO_PORT
MONGO_ADMIN_USERNAME = env.MONGO_ADMIN_USERNAME
MONGO_ADMIN_PASSWORD = env.MONGO_ADMIN_PASSWORD

admin_client = MongoClient(MONGO_HOST,
                           MONGO_PORT,
                           username=MONGO_ADMIN_USERNAME,
                           password=MONGO_ADMIN_PASSWORD)
db = admin_client['ufc']
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
        if request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = 0
        print('User id is: ', user_id)
        offset = request.data['offset']
        triggered_at = match_checker.get_triggered_at()
        if user_id > 0:
            diners, diners_count = match_searcher.get_search_result(condition, triggered_at, offset, request.user)
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
        if request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = 0
        triggered_at = match_checker.get_triggered_at()
        if user_id > 0:
            diners = match_searcher.get_random(triggered_at, request.user)
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
        triggered_at = match_checker.get_triggered_at()
        if request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = 0
        if uuid_ue and uuid_fp:
            if user_id == 0:
                diner = match_dinerinfo.get_diner(uuid_ue, 'ue', triggered_at)
            else:
                diner = match_dinerinfo.get_diner(uuid_ue, 'ue', triggered_at, request.user)
            if (not diner) and (user_id == 0):
                diner = match_dinerinfo.get_diner(uuid_fp, 'fp', triggered_at)
            else:
                diner = match_dinerinfo.get_diner(uuid_fp, 'fp', triggered_at, request.user)
            if not diner:
                return Response({'data': '404'})
            results = MatchSerializer(diner, many=False).data
            stop = time.time()
            print('get DinerInfo took: ', stop - start, 's.')
            return Response({'data': results})
        elif uuid_ue:
            if user_id == 0:
                diner = match_dinerinfo.get_diner(uuid_ue, 'ue', triggered_at)
            else:
                diner = match_dinerinfo.get_diner(uuid_ue, 'ue', triggered_at, request.user)
            if diner:
                results = MatchSerializer(diner, many=False).data
                stop = time.time()
                print('get DinerInfo took: ', stop - start, 's.')
                return Response({'data': results})
        elif uuid_fp:
            if user_id == 0:
                diner = match_dinerinfo.get_diner(uuid_fp, 'fp', triggered_at)
            else:
                diner = match_dinerinfo.get_diner(uuid_fp, 'fp', triggered_at, request.user)
            results = MatchSerializer(diner, many=False).data
            stop = time.time()
            print('get DinerInfo took: ', stop - start, 's.')
            return Response({'data': results})
        else:
            return Response({'message': 'need diner_id'})


class Filters(views.APIView):
    def get(self, request):
        start = time.time()
        triggered_at = match_checker.get_triggered_at()
        filters = match_filters.get_filters(triggered_at)
        data = FilterSerializer(filters, many=False).data
        stop = time.time()
        print('get Filters took: ', stop - start, 's.')
        return Response({'data': data})


class FavoritesAPI(views.APIView):
    def post(self, request):
        request_data = request.data
        if request.user.is_authenticated:
            pass
        else:
            return Response({'message': 'need login'})
        source = request_data['source']
        if source == 'ue':
            uuid = request_data['uuid_ue']
        if source == 'fp':
            uuid = request_data['uuid_fp']
        activate = request_data['activate']
        favorite_sqlrecord = Favorites.manager.update_favorite(request.user, uuid, activate)
        print(favorite_sqlrecord)
        return Response({'message': 'success'})

    def get(self, request):
        if request.user.is_authenticated:
            pass
        else:
            return Response({'message': 'need login'})
        offset = int(self.request.query_params.get('offset', None))
        favorites = Favorites.manager.get_favorites(request.user, offset)
        if not favorites:
            return Response({
                'is_data': False
            })
        diners = []
        triggered_at = match_checker.get_triggered_at()
        if offset + 6 < len(favorites):
            has_more = True
        else:
            has_more = False
        if has_more:
            next_offset = offset + 6
        else:
            next_offset = 0
        or_conditions = []
        for favorite in favorites[offset: offset+6]:
            if len(favorite) > 8:
                uuid_ue = favorite
                match = {"uuid_ue": uuid_ue}
                or_conditions.append(match)
            else:
                uuid_fp = favorite
                match = {"uuid_fp": uuid_fp}
                or_conditions.append(match)
        match_condition = [
            {
                "$match": {
                    "triggered_at": triggered_at
                }
            }, {
                "$match": {
                    "$or": or_conditions
                }
            }
            ]
        diners = list(db['matched'].aggregate(match_condition))
        if len(diners) == 0:
            return Response({
                'is_data': False
            })
        for diner in diners:
            diner['favorite'] = True
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
    if request.user.is_authenticated:
        pprint.pprint(request.user)
        return render(request, 'Diner_app/dinerlist.html', {'user_is_authenticated': True, 'current_page': '店家列表'})
    else:
        return render(request, 'Diner_app/dinerlist.html', {'user_is_authenticated': False, 'current_page': '店家列表'})


def dinerinfo(request):
    if request.user.is_authenticated:
        return render(request, 'Diner_app/dinerinfo.html', {'user_is_authenticated': True, 'current_page': '店家資訊'})
    else:
        return render(request, 'Diner_app/dinerinfo.html', {'user_is_authenticated': False, 'current_page': '店家資訊'})


def favorites(request):
    if request.user.is_authenticated:
        return render(request, 'Diner_app/favorites.html', {'user_is_authenticated': True, 'current_page': '收藏'})
    else:
        return redirect('/user/login')


def forSSL(request):
    filepath = 'F6B43E81B6BB7366178E7DE03B1BB0FC.txt'
    f = open(filepath, 'r')
    file_content = f.read()
    f.close()
    return HttpResponse(file_content, content_type='text/plain')
