# for django
from django.shortcuts import render, redirect

# for django api rate limiter
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit

# for django restful api
from rest_framework import views
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

# for mongo db control
from pymongo import MongoClient

# for timing
import datetime

# home-made modules
# for mysql and mongo query
from .models import Favorites, Noteq
from .mongo_query import DashBoardQuery, FavoritesQuery, FiltersQuery, SearcherQuery, DinerInfoQuery

# for return data to frontend
from .serializers import DinerSerializer, FilterSerializer, DashBoardSerializer

# for gile handling
import env
from Diner_app import conf

# my utility belt
import utils

# Create your views here.
MONGO_EC2_URI = env.MONGO_EC2_URI
DB_NAME = conf.DB_NAME
LOG_COLLECTION = conf.LOG_COLLECTION
MATCHED_COLLECTION = conf.MATCHED_COLLECTION
MATCH = conf.MATCH
TRIGGERED_BY_LIST = conf.TRIGGERED_BY_LIST
admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client[DB_NAME]


class DashBoardAPI(views.APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        dashboard_waiter = DashBoardQuery(db, LOG_COLLECTION, TRIGGERED_BY_LIST)
        end_date = datetime.datetime.strptime(request.data['end_date'], '%Y-%m-%d %H:%M')
        start_date = datetime.datetime.strptime(request.data['start_date'], '%Y-%m-%d %H:%M')
        end_time = datetime.datetime.combine(end_date, datetime.time.max)
        start_time = datetime.datetime.combine(start_date, datetime.time.min)
        # start_time = datetime.datetime.combine(start_date, datetime.time(12, 30, 0))
        result = dashboard_waiter.main(end_time, start_time)
        data = DashBoardSerializer(result, many=False).data
        return Response({
            'data': data
        })


class DinerSearchAPI(views.APIView):
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
        checker = utils.Checker(db, MATCHED_COLLECTION, LOG_COLLECTION, r_triggered_by=MATCH)
        triggered_at = checker.triggered_at

        searcher = SearcherQuery(db, MATCHED_COLLECTION)
        if user_id > 0:
            diners, diners_count = searcher.get_search_result(condition, triggered_at, offset, request.user)
        else:
            diners, diners_count = searcher.get_search_result(condition, triggered_at, offset)

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
        data = DinerSerializer(diners, many=True).data
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


class DinerShuffleAPI(views.APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        # start = time.time()
        if request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = 0
        checker = utils.Checker(db, MATCHED_COLLECTION, LOG_COLLECTION, r_triggered_by=MATCH)
        triggered_at = checker.triggered_at
        searcher = SearcherQuery(db, MATCHED_COLLECTION)
        if user_id > 0:
            diners = searcher.get_random(triggered_at, request.user)
        else:
            diners = searcher.get_random(triggered_at)
        has_more = False
        next_offset = 0
        diners = diners
        data = DinerSerializer(diners, many=True).data
        # stop = time.time()
        # print('post DinerSearch took: ', stop - start, 's.')
        return Response({
            'next_offset': next_offset,
            'has_more': has_more,
            'max_page': 1,
            'data_count': len(diners),
            'data': data
            })


class DinerInfoAPI(views.APIView):
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
        info_waiter = DinerInfoQuery(db, MATCHED_COLLECTION)
        if user_id == 0:
            diner = info_waiter.get_diner(uuid_ue, uuid_fp)
        else:
            diner = info_waiter.get_diner(uuid_ue, uuid_fp, request.user)
        if not diner:
            return Response({'data': '404'})
        results = DinerSerializer(diner, many=False).data
        # stop = time.time()
        # print('get DinerInfo took: ', stop - start, 's.')
        return Response({'data': results})


class FiltersAPI(views.APIView):

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='GET'))
    def get(self, request):
        # start = time.time()
        checker = utils.Checker(db, MATCHED_COLLECTION, LOG_COLLECTION, r_triggered_by=MATCH)
        triggered_at = checker.triggered_at
        filters_waiter = FiltersQuery(db, MATCHED_COLLECTION)
        filters = filters_waiter.get_filters(triggered_at)
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

        user = request.user
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

        favorites_waiter = FavoritesQuery(db, MATCHED_COLLECTION)
        diners = favorites_waiter.get_favorites_diners(user, offset)
        if not diners:
            return Response({
                'is_data': False
            })

        if offset + 6 < favorites_count:
            has_more = True
        else:
            has_more = False
        if has_more:
            next_offset = offset + 6
        else:
            next_offset = 0

        data = DinerSerializer(diners, many=True).data
        response = Response({
            'is_data': True,
            'next_offset': next_offset,
            'has_more': has_more,
            'max_page': favorites_count // 6,
            'data_count': len(diners),
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


def dinerlist_view(request):
    if request.user.is_authenticated:
        pprint.pprint(request.user)
        return render(request, 'Diner_app/dinerlist.html', {'user_is_authenticated': True, 'current_page': '店家列表'})
    else:
        return render(request, 'Diner_app/dinerlist.html', {'user_is_authenticated': False, 'current_page': '店家列表'})


def dinerinfo_view(request):
    if request.user.is_authenticated:
        return render(request, 'Diner_app/dinerinfo.html', {'user_is_authenticated': True, 'current_page': '店家資訊'})
    else:
        return render(request, 'Diner_app/dinerinfo.html', {'user_is_authenticated': False, 'current_page': '店家資訊'})


def favorites_view(request):
    if request.user.is_authenticated:
        return render(request, 'Diner_app/favorites.html', {'user_is_authenticated': True, 'current_page': '收藏'})
    else:
        return redirect('/user/login')


def dashboard_view(request):
    if request.user.is_authenticated:
        return render(request, 'Diner_app/dashboard.html', {'user_is_authenticated': True, 'current_page': '儀表板'})
    else:
        return render(request, 'Diner_app/dashboard.html', {'user_is_authenticated': False, 'current_page': '儀表板'})


def test_500_view():
    return Response({'message': 'success'})

# def forSSL(request):
#     file_content = env.VERIFY_DOMAIN
#     return HttpResponse(file_content, content_type='text/plain')
