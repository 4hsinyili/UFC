# from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
# from django.http import HttpResponse
from ratelimit.decorators import ratelimit
from rest_framework import views
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .serializers import MatchSerializer, FilterSerializer, DashBoardSerializer
# from django.db import transaction
# from rest_framework.generics import GenericAPIView
from .models import MatchChecker, MatchFilters, MatchSearcher, MatchDinerInfo, Favorites, Noteq, DashBoardModel
import env
from pymongo import MongoClient
# import time
import pprint
import boto3
import datetime

# Create your views here.
MONGO_EC2_URI = env.MONGO_EC2_URI
admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client['ufc']
cloudwatch = boto3.client('cloudwatch')
match_checker = MatchChecker(db, 'matched', 'match')
match_searcher = MatchSearcher(db, 'matched')
match_dinerinfo = MatchDinerInfo(db, 'matched')
match_filters = MatchFilters(db, 'matched')


class DashBoardView(views.APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        model = DashBoardModel(db, cloudwatch)
        end_date = datetime.datetime.strptime(request.data['end_date'], '%Y-%m-%d %H:%M')
        start_date = datetime.datetime.strptime(request.data['start_date'], '%Y-%m-%d %H:%M')
        end_time = datetime.datetime.combine(end_date, datetime.time.max)
        start_time = datetime.datetime.combine(start_date, datetime.time.min)
        # start_time = datetime.datetime.combine(start_date, datetime.time(12, 30, 0))
        result = model.get_data(end_time, start_time)
        data = DashBoardSerializer(result, many=False).data
        return Response({
            'data': data
        })


class DinerSearch(views.APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        # start = time.time()
        condition = request.data['condition']
        if request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = 0
        # print('User id is: ', user_id)
        offset = request.data['offset']
        triggered_at = match_checker.get_triggered_at()
        if user_id > 0:
            diners, diners_count = match_searcher.get_search_result(condition, triggered_at, offset, request.user)
        else:
            diners, diners_count = match_searcher.get_search_result(condition, triggered_at, offset)

        if not diners:
            return Response({
                'no_data': 1
            })

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
        # stop = time.time()
        # print('post DinerSearch took: ', stop - start, 's.')
        return Response({
            'next_offset': next_offset,
            'has_more': has_more,
            'max_page': diners_count // 6,
            'data_count': len(diners),
            'data': data,
            'no_data': 0
            })


class DinerShuffle(views.APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        # start = time.time()
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
        # stop = time.time()
        # print('post DinerSearch took: ', stop - start, 's.')
        return Response({
            'next_offset': next_offset,
            'has_more': has_more,
            'max_page': 1,
            'data_count': len(diners),
            'data': data
            })


class DinerInfo(views.APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='GET'))
    def get(self, request):
        # start = time.time()
        uuid_ue = self.request.query_params.get('uuid_ue', None)
        uuid_fp = self.request.query_params.get('uuid_fp', None)
        if request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = 0
        if uuid_ue is None:
            uuid_ue = ''
        if uuid_fp is None:
            uuid_fp = ''
        if user_id == 0:
            diner = match_dinerinfo.get_diner(uuid_ue, uuid_fp)
        else:
            diner = match_dinerinfo.get_diner(uuid_ue, uuid_fp, request.user)
        if not diner:
            return Response({'data': '404'})
        results = MatchSerializer(diner, many=False).data
        # stop = time.time()
        # print('get DinerInfo took: ', stop - start, 's.')
        return Response({'data': results})


class Filters(views.APIView):

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='GET'))
    def get(self, request):
        # start = time.time()
        triggered_at = match_checker.get_triggered_at()
        filters = match_filters.get_filters(triggered_at)
        data = FilterSerializer(filters, many=False).data
        # stop = time.time()
        # print('get Filters took: ', stop - start, 's.')
        return Response({'data': data})


class FavoritesAPI(views.APIView):

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        request_data = request.data
        if request.user.is_authenticated:
            pass
        else:
            return Response({'message': 'need login'})
        uuid_ue = request_data['uuid_ue']
        uuid_fp = request_data['uuid_fp']
        activate = request_data['activate']
        favorite_sqlrecord = Favorites.manager.update_favorite(request.user, uuid_ue, uuid_fp, activate)
        favorites_count = Favorites.manager.count_favorites(request.user)
        # print(favorite_sqlrecord)
        response = Response({'message': 'update favorite success', 'result': str(favorite_sqlrecord)})
        response.set_cookie('ufc_favorites_count', favorites_count)
        return response

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='GET'))
    def get(self, request):
        if request.user.is_authenticated:
            pass
        else:
            return Response({'message': 'need login'})
        offset = int(self.request.query_params.get('offset', None))
        favorites_count = request.COOKIES.get('ufc_favorites_count')
        if favorites_count is None:
            favorites_count = Favorites.manager.count_favorites(request.user)
        else:
            favorites_count = int(favorites_count)
        if favorites_count == 0:
            response = Response({
                'is_data': False
            })
            response.set_cookie('ufc_favorites_count', favorites_count)
            return response
        if not favorites:
            return Response({
                'is_data': False
            })
        diners = []
        if offset + 6 < favorites_count:
            has_more = True
        else:
            has_more = False
        if has_more:
            next_offset = offset + 6
        else:
            next_offset = 0
        or_conditions = []
        for favorite in favorites[offset: offset+6]:
            uuid_ue = favorite[0]
            uuid_fp = favorite[1]
            match = {"uuid_ue": uuid_ue, "uuid_fp": uuid_fp}
            or_conditions.append(match)
        match_condition = [
            {
                "$match": {
                    "$or": or_conditions
                }
            },
            {
                "$sort": {"triggered_at": 1}
            },
            {
                "$group": {
                    "_id": {"uuid_ue": "$uuid_ue", "uuid_fp": "$uuid_fp"},
                    "triggered_at": {"$last": "$triggered_at"},
                    "data": {
                        "$push": {
                            "uuid_ue": "$uuid_ue",
                            "uuid_fp": "$uuid_fp",
                            "title_ue": "$title_ue",
                            "title_fp": "$title_fp",
                            "triggered_at": "$triggered_at",
                            "image_ue": "$image_ue",
                            "link_ue": "$link_ue",
                            "rating_ue": "$rating_ue",
                            "view_count_ue": "$view_count_ue",
                            "image_fp": "$image_fp",
                            "link_fp": "$link_fp",
                            "rating_fp": "$rating_fp",
                            "view_count_fp": "$view_count_fp",
                            "uuid_gm": "$uuid_gm",
                            "link_gm": "$link_gm",
                            "rating_gm": "$rating_gm",
                            "view_count_gm": "$view_count_gm"
                        }
                    }
                }
            }
        ]
        diners = list(db['matched'].aggregate(match_condition))
        if len(diners) == 0:
            return Response({
                'is_data': False
            })
        results = []
        for diner_dict in diners:
            diner = diner_dict['data'][-1]
            diner['favorite'] = True
            results.append(diner)
        data = MatchSerializer(results, many=True).data
        return Response({
            'is_data': True,
            'next_offset': next_offset,
            'has_more': has_more,
            'max_page': 1,
            'data_count': len(results),
            'data': data
            })
        response.set_cookie('ufc_favorites_count', favorites_count)
        return response


class NoteqAPI(views.APIView):

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        request_data = request.data
        if request.user.is_authenticated:
            pass
        else:
            return Response({'message': 'need login'})
        uuid_ue = request_data['uuid_ue']
        uuid_fp = request_data['uuid_fp']
        uuid_gm = request_data['uuid_gm']
        noteq_sqlrecord = Noteq.manager.add_noteq(request.user, uuid_ue, uuid_fp, uuid_gm)
        # print(noteq_sqlrecord)
        return Response({'message': 'update favorite success', 'result': str(noteq_sqlrecord)})


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


def dashboard(request):
    if request.user.is_authenticated:
        return render(request, 'Diner_app/dashboard.html', {'user_is_authenticated': True, 'current_page': '儀表板'})
    else:
        return render(request, 'Diner_app/dashboard.html', {'user_is_authenticated': False, 'current_page': '儀表板'})


def test_500():
    return Response({'message': 'success'})

# def forSSL(request):
#     file_content = env.VERIFY_DOMAIN
#     return HttpResponse(file_content, content_type='text/plain')
